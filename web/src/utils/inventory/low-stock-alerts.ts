/**
 * Low Stock Alert System
 * Issue #110: Inventory Management - Low Stock Notifications
 * 
 * Provides proactive notifications when inventory items fall below minimum quantities
 */

import { createClient } from "@supabase/supabase-js";

interface LowStockAlert {
  item_id: string;
  item_name: string;
  current_quantity: number;
  min_quantity: number;
  quantity_needed: number;
  location: string;
  urgency: "critical" | "warning";
}

export async function getLowStockItems(
  userId: string
): Promise<LowStockAlert[]> {
  const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );

  const { data: items, error } = await supabase
    .from("user_inventory")
    .select("*")
    .eq("user_id", userId)
    .not("min_quantity", "is", null);

  if (error) throw error;

  // Filter items below minimum quantity
  const lowStockItems: LowStockAlert[] = items
    .filter(
      (item: Record<string, unknown>) => item.quantity as number <= (item.min_quantity as number)
    )
    .map((item: Record<string, unknown>): LowStockAlert => ({
      item_id: item.id as string,
      item_name: item.item_name as string,
      current_quantity: item.quantity as number,
      min_quantity: item.min_quantity as number,
      quantity_needed: Math.ceil((item.min_quantity as number) * 1.5 - (item.quantity as number)), // Suggest restock to 1.5x min
      location: item.location as string,
      urgency:
        (item.quantity as number) <= (item.min_quantity as number) * 0.5 ? "critical" : "warning",
    }))
    .sort(
      (a: LowStockAlert, b: LowStockAlert) =>
        a.current_quantity - b.current_quantity
    );

  return lowStockItems;
}

// Get summary of low stock items by location
export async function getLowStockSummaryByLocation(userId: string) {
  const items = await getLowStockItems(userId);

  const summary: Record<string, { critical: number; warning: number }> = {};

  for (const item of items) {
    if (!summary[item.location]) {
      summary[item.location] = { critical: 0, warning: 0 };
    }
    summary[item.location][item.urgency]++;
  }

  return summary;
}

// Auto-generate shopping list from low stock items
export async function generateRestockingList(userId: string): Promise<string> {
  const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );

  const lowStockItems = await getLowStockItems(userId);

  if (lowStockItems.length === 0) {
    return "No items need restocking";
  }

  // Create new shopping list
  const { data: newList, error: listError } = await supabase
    .from("shopping_lists")
    .insert({
      user_id: userId,
      name: `Auto-generated Restock List - ${new Date().toLocaleDateString()}`,
      description: "Auto-generated from low stock alerts",
    })
    .select()
    .single();

  if (listError) throw listError;

  // Add items to shopping list
  const items = lowStockItems.map((item) => ({
    shopping_list_id: newList.id,
    ingredient_id: null, // Can be looked up from item name
    item_name: item.item_name,
    quantity: item.quantity_needed,
    unit: "units",
    category: item.location,
    is_checked: false,
  }));

  const { error: itemsError } = await supabase
    .from("shopping_list_items")
    .insert(items);

  if (itemsError) throw itemsError;

  return `Restocking list created with ${items.length} items`;
}

// Set minimum quantity for an item
export async function updateMinimumQuantity(
  itemId: string,
  minQuantity: number
): Promise<void> {
  const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );

  const { error } = await supabase
    .from("user_inventory")
    .update({ min_quantity: minQuantity })
    .eq("id", itemId);

  if (error) throw error;
}

// Send notification for low stock
export async function notifyLowStock(userId: string): Promise<void> {
  const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );

  const lowStockItems = await getLowStockItems(userId);

  if (lowStockItems.length === 0) return;

  // Create notification record
  for (const item of lowStockItems) {
    await supabase.from("low_stock_notifications").insert({
      user_id: userId,
      inventory_id: item.item_id,
      item_name: item.item_name,
      current_quantity: item.current_quantity,
      min_quantity: item.min_quantity,
      urgency: item.urgency,
      created_at: new Date().toISOString(),
    });
  }
}
