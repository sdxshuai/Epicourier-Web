"use client";

import { useState, useEffect, useCallback } from "react";
import { Package, Lightbulb, Loader2, Plus } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import {
  LocationTabs,
  InventorySearchBar,
  ExpiringSoonBanner,
  InventoryItemCard,
  AddInventoryModal,
  EditInventoryModal,
  DeleteInventoryDialog,
} from "@/components/inventory";
import type {
  InventoryLocation,
  InventoryItemWithDetails,
  InventorySummary,
} from "@/types/data";

export default function InventoryPage() {
  const [items, setItems] = useState<InventoryItemWithDetails[]>([]);
  const [summary, setSummary] = useState<InventorySummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeLocation, setActiveLocation] = useState<InventoryLocation | "all">("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<InventoryItemWithDetails | null>(null);
  const [deletingItem, setDeletingItem] = useState<InventoryItemWithDetails | null>(null);
  const [suggesting, setSuggesting] = useState(false);

  const { toast } = useToast();

  const fetchInventory = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (activeLocation !== "all") {
        params.set("location", activeLocation);
      }
      if (searchQuery.trim()) {
        params.set("search", searchQuery.trim());
      }

      const response = await fetch("/api/inventory?" + params.toString());

      if (!response.ok) {
        if (response.status === 401) {
          toast({
            title: "Authentication Required",
            description: "Please sign in to view your inventory",
            variant: "destructive",
          });
          return;
        }
        throw new Error("Failed to fetch inventory");
      }

      const data = await response.json();
      setItems(data.items || []);
      setSummary(data.summary || null);
    } catch (error) {
      console.error("Error fetching inventory:", error);
      toast({
        title: "Error",
        description: "Failed to load inventory",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }, [activeLocation, searchQuery, toast]);

  useEffect(() => {
    fetchInventory();
  }, [fetchInventory]);

  const handleSuggestRecipes = async () => {
    if (items.length === 0) {
      toast({
        title: "Empty Inventory",
        description: "Add some ingredients to your inventory first",
        variant: "destructive",
      });
      return;
    }

    setSuggesting(true);
    try {
      await new Promise((resolve) => setTimeout(resolve, 1500));
      toast({
        title: "AI Recommendations",
        description: "Recipe suggestions coming in Issue #97",
      });
    } catch (error) {
      console.error("Error suggesting recipes:", error);
      toast({
        title: "Error",
        description: "Failed to generate recipe suggestions",
        variant: "destructive",
      });
    } finally {
      setSuggesting(false);
    }
  };

  const handleViewExpiring = () => {
    const expiredCount = summary?.expired || 0;
    const expiringSoonCount = summary?.expiring_soon || 0;
    toast({
      title: "Expiring Items",
      description: expiredCount + " expired, " + expiringSoonCount + " expiring soon",
    });
  };

  const locationCounts = summary
    ? {
        all: summary.total_items,
        pantry: summary.by_location.pantry,
        fridge: summary.by_location.fridge,
        freezer: summary.by_location.freezer,
        other: summary.by_location.other,
      }
    : undefined;

  if (loading && items.length === 0) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="flex items-center gap-2 text-gray-600">
          <Loader2 className="size-5 animate-spin" />
          <span className="font-semibold">Loading inventory...</span>
        </div>
      </div>
    );
  }

  const totalItems = summary?.total_items || 0;
  const lowStockCount = summary?.low_stock || 0;

  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-8">
      <div className="brutalism-banner mb-6 p-5">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Package className="size-8" />
            <div>
              <h1 className="brutalism-title text-2xl">Inventory</h1>
              <p className="text-sm font-semibold text-gray-700">
                {totalItems} {totalItems === 1 ? "item" : "items"}
                {lowStockCount > 0 ? " - " + lowStockCount + " low stock" : ""}
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setIsAddModalOpen(true)}
              className="brutalism-button-primary flex items-center gap-2 px-4 py-2"
            >
              <Plus className="size-4" />
              <span>Add Item</span>
            </button>
            <button
              onClick={handleSuggestRecipes}
              disabled={suggesting || items.length === 0}
              className="brutalism-button-secondary flex items-center gap-2 px-4 py-2 disabled:opacity-50"
            >
              {suggesting ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  <span>Suggesting...</span>
                </>
              ) : (
                <>
                  <Lightbulb className="size-4" />
                  <span>Suggest Recipes</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {summary && (summary.expired > 0 || summary.expiring_soon > 0) && (
        <ExpiringSoonBanner
          expiredCount={summary.expired}
          expiringCount={summary.expiring_soon}
          onViewAll={handleViewExpiring}
          className="mb-6"
        />
      )}

      <LocationTabs
        activeLocation={activeLocation}
        onLocationChange={setActiveLocation}
        counts={locationCounts}
        className="mb-4"
      />

      <InventorySearchBar
        value={searchQuery}
        onChange={setSearchQuery}
        className="mb-6"
      />

      {items.length === 0 ? (
        <div className="brutalism-panel flex flex-col items-center justify-center p-12 text-center">
          <Package className="mb-4 size-16 text-gray-400" />
          <h2 className="brutalism-heading mb-2 text-xl">
            {searchQuery ? "No Results Found" : "No Inventory Items Yet"}
          </h2>
          <p className="mb-6 text-gray-600">
            {searchQuery
              ? "No items match your search"
              : "Add ingredients to your inventory to track what you have at home"}
          </p>
          {!searchQuery && (
            <button
              onClick={() => setIsAddModalOpen(true)}
              className="brutalism-button-primary flex items-center gap-2 px-6 py-3"
            >
              <Plus className="size-5" />
              <span>Add First Item</span>
            </button>
          )}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {items.map((item) => (
            <InventoryItemCard
              key={item.id}
              item={item}
              onEdit={setEditingItem}
              onDelete={setDeletingItem}
            />
          ))}
        </div>
      )}

      <AddInventoryModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onSuccess={() => {
          setIsAddModalOpen(false);
          fetchInventory();
        }}
      />

      <EditInventoryModal
        isOpen={!!editingItem}
        item={editingItem}
        onClose={() => setEditingItem(null)}
        onSuccess={() => {
          setEditingItem(null);
          fetchInventory();
        }}
      />

      <DeleteInventoryDialog
        isOpen={!!deletingItem}
        item={deletingItem}
        onClose={() => setDeletingItem(null)}
        onSuccess={() => {
          setDeletingItem(null);
          fetchInventory();
        }}
      />
    </div>
  );
}
