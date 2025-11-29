"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  ShoppingCart,
  Plus,
  Loader2,
  Archive,
  ArchiveRestore,
  MoreVertical,
  Trash2,
  Edit2,
  CheckCircle2,
  ClipboardList,
  Calendar,
  ArrowRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useToast } from "@/hooks/use-toast";
import CreateShoppingListModal from "@/components/shopping/CreateShoppingListModal";
import type { ShoppingListWithStats } from "@/types/data";

/**
 * Shopping Lists Page - displays all user's shopping lists
 *
 * Features:
 * - View all shopping lists with item counts and progress
 * - Create new shopping lists
 * - Archive/Delete lists
 * - Navigate to list details
 * - Consistent dashboard design style
 */
export default function ShoppingListsPage() {
  const router = useRouter();
  const { toast } = useToast();

  const [lists, setLists] = useState<ShoppingListWithStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showArchived, setShowArchived] = useState(false);

  // Fetch shopping lists
  const fetchLists = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/shopping-lists");
      if (!res.ok) {
        if (res.status === 401) {
          router.push("/signin");
          return;
        }
        throw new Error("Failed to fetch shopping lists");
      }
      const data: ShoppingListWithStats[] = await res.json();
      setLists(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    fetchLists();
  }, [fetchLists]);

  // Handle list creation
  const handleCreateList = async (name: string, description?: string) => {
    try {
      const res = await fetch("/api/shopping-lists", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, description }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.error || "Failed to create list");
      }

      toast({
        title: "List created",
        description: `"${name}" has been created.`,
      });

      setShowCreateModal(false);
      fetchLists();
    } catch (err) {
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : "Failed to create list",
        variant: "destructive",
      });
    }
  };

  // Handle archive toggle
  const handleArchive = async (list: ShoppingListWithStats) => {
    try {
      const res = await fetch(`/api/shopping-lists/${list.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_archived: !list.is_archived }),
      });

      if (!res.ok) {
        throw new Error("Failed to update list");
      }

      toast({
        title: list.is_archived ? "List restored" : "List archived",
        description: `"${list.name}" has been ${list.is_archived ? "restored" : "archived"}.`,
      });

      fetchLists();
    } catch (err) {
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : "Failed to update list",
        variant: "destructive",
      });
    }
  };

  // Handle delete
  const handleDelete = async (list: ShoppingListWithStats) => {
    if (!confirm(`Are you sure you want to delete "${list.name}"? This cannot be undone.`)) {
      return;
    }

    try {
      const res = await fetch(`/api/shopping-lists/${list.id}`, {
        method: "DELETE",
      });

      if (!res.ok) {
        throw new Error("Failed to delete list");
      }

      toast({
        title: "List deleted",
        description: `"${list.name}" has been deleted.`,
      });

      fetchLists();
    } catch (err) {
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : "Failed to delete list",
        variant: "destructive",
      });
    }
  };

  // Filter lists based on archived state
  const activeLists = lists.filter((list) => !list.is_archived);
  const archivedLists = lists.filter((list) => list.is_archived);
  const filteredLists = showArchived ? archivedLists : activeLists;

  // Calculate stats
  const totalItems = activeLists.reduce((sum, list) => sum + list.item_count, 0);
  const checkedItems = activeLists.reduce((sum, list) => sum + list.checked_count, 0);

  // Format date
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === today.toDateString()) return "Today";
    if (date.toDateString() === yesterday.toDateString()) return "Yesterday";
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  };

  // Loading state
  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="flex items-center gap-2 text-gray-600">
          <Loader2 className="size-5 animate-spin" />
          <span className="font-semibold">Loading shopping lists...</span>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex min-h-[400px] items-center justify-center p-4">
        <div className="rounded-xl border bg-card p-6 text-center max-w-md">
          <p className="font-bold mb-2 text-red-600">Error</p>
          <p className="text-sm text-muted-foreground">{error}</p>
          <Button onClick={fetchLists} className="mt-4">
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold flex items-center gap-2">
            <ShoppingCart className="size-7 text-emerald-500" />
            Shopping Lists
          </h1>
          <p className="text-muted-foreground">Manage your grocery shopping</p>
        </div>
        <Button onClick={() => setShowCreateModal(true)} className="gap-2">
          <Plus className="size-4" />
          New List
        </Button>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <div className="p-4 rounded-xl border bg-card shadow-sm">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-emerald-50 dark:bg-emerald-950/30">
              <ClipboardList className="size-5 text-emerald-600 dark:text-emerald-400" />
            </div>
            <div>
              <p className="text-2xl font-bold">{activeLists.length}</p>
              <p className="text-xs text-muted-foreground">Active Lists</p>
            </div>
          </div>
        </div>

        <div className="p-4 rounded-xl border bg-card shadow-sm">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-50 dark:bg-blue-950/30">
              <ShoppingCart className="size-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <p className="text-2xl font-bold">{totalItems}</p>
              <p className="text-xs text-muted-foreground">Total Items</p>
            </div>
          </div>
        </div>

        <div className="p-4 rounded-xl border bg-card shadow-sm">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-green-50 dark:bg-green-950/30">
              <CheckCircle2 className="size-5 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <p className="text-2xl font-bold">{checkedItems}</p>
              <p className="text-xs text-muted-foreground">Checked Off</p>
            </div>
          </div>
        </div>

        <div className="p-4 rounded-xl border bg-card shadow-sm">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-gray-50 dark:bg-gray-800">
              <Archive className="size-5 text-gray-600 dark:text-gray-400" />
            </div>
            <div>
              <p className="text-2xl font-bold">{archivedLists.length}</p>
              <p className="text-xs text-muted-foreground">Archived</p>
            </div>
          </div>
        </div>
      </div>

      {/* Tab Toggle */}
      <div className="flex items-center gap-2">
        <Button
          variant={!showArchived ? "default" : "outline"}
          size="sm"
          onClick={() => setShowArchived(false)}
          className="gap-1"
        >
          <ClipboardList className="size-4" />
          Active ({activeLists.length})
        </Button>
        <Button
          variant={showArchived ? "default" : "outline"}
          size="sm"
          onClick={() => setShowArchived(true)}
          className="gap-1"
        >
          <Archive className="size-4" />
          Archived ({archivedLists.length})
        </Button>
      </div>

      {/* Lists Grid */}
      {filteredLists.length === 0 ? (
        <div className="rounded-xl border bg-card p-12 text-center">
          <ShoppingCart className="mx-auto size-12 text-muted-foreground/50" />
          <h3 className="mt-4 font-semibold text-lg">
            {showArchived ? "No archived lists" : "No shopping lists yet"}
          </h3>
          <p className="mt-2 text-muted-foreground text-sm">
            {showArchived
              ? "Archived lists will appear here"
              : "Create your first shopping list to get started"}
          </p>
          {!showArchived && (
            <Button onClick={() => setShowCreateModal(true)} className="mt-6 gap-2">
              <Plus className="size-4" />
              Create List
            </Button>
          )}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filteredLists.map((list) => (
            <div
              key={list.id}
              className="group rounded-xl border bg-card shadow-sm hover:shadow-md transition-all cursor-pointer"
              onClick={() => router.push(`/dashboard/shopping/${list.id}`)}
            >
              <div className="p-5">
                {/* Header */}
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold truncate">{list.name}</h3>
                    {list.description && (
                      <p className="mt-1 truncate text-sm text-muted-foreground">
                        {list.description}
                      </p>
                    )}
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="size-8 opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        <MoreVertical className="size-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-40">
                      <DropdownMenuItem
                        onClick={(e) => {
                          e.stopPropagation();
                          router.push(`/dashboard/shopping/${list.id}`);
                        }}
                      >
                        <Edit2 className="mr-2 size-4" />
                        Edit
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={(e) => {
                          e.stopPropagation();
                          handleArchive(list);
                        }}
                      >
                        {list.is_archived ? (
                          <>
                            <ArchiveRestore className="mr-2 size-4" />
                            Restore
                          </>
                        ) : (
                          <>
                            <Archive className="mr-2 size-4" />
                            Archive
                          </>
                        )}
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete(list);
                        }}
                        className="text-red-600 focus:text-red-600"
                      >
                        <Trash2 className="mr-2 size-4" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>

                {/* Progress */}
                <div className="mt-4">
                  <div className="flex items-center justify-between text-sm mb-2">
                    <span className="text-muted-foreground">
                      {list.checked_count} / {list.item_count} items
                    </span>
                    <span className="font-medium">{list.progress_percentage}%</span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-emerald-500 rounded-full transition-all"
                      style={{ width: `${list.progress_percentage}%` }}
                    />
                  </div>
                </div>

                {/* Footer */}
                <div className="mt-4 flex items-center justify-between text-xs text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Calendar className="size-3" />
                    {formatDate(list.updated_at)}
                  </span>
                  {list.item_count > 0 && list.checked_count === list.item_count ? (
                    <span className="flex items-center gap-1 text-emerald-500">
                      <CheckCircle2 className="size-4" />
                      Complete
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-primary opacity-0 group-hover:opacity-100 transition-opacity">
                      View <ArrowRight className="size-3" />
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Quick Actions */}
      {activeLists.length > 0 && !showArchived && (
        <div className="rounded-xl border bg-card p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Calendar className="size-5 text-blue-500" />
              <h3 className="font-semibold">Quick Actions</h3>
            </div>
          </div>
          <div className="grid sm:grid-cols-2 gap-3">
            <Link
              href="/dashboard/calendar"
              className="flex items-center gap-3 p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
            >
              <Calendar className="size-5 text-blue-500" />
              <div className="flex-1">
                <p className="font-medium text-sm">Generate from Calendar</p>
                <p className="text-xs text-muted-foreground">
                  Auto-create list from your meal plan
                </p>
              </div>
              <ArrowRight className="size-4 text-muted-foreground" />
            </Link>
            <Link
              href="/dashboard/recipes"
              className="flex items-center gap-3 p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
            >
              <ShoppingCart className="size-5 text-emerald-500" />
              <div className="flex-1">
                <p className="font-medium text-sm">Add from Recipe</p>
                <p className="text-xs text-muted-foreground">Add ingredients from any recipe</p>
              </div>
              <ArrowRight className="size-4 text-muted-foreground" />
            </Link>
          </div>
        </div>
      )}

      {/* Create Modal */}
      <CreateShoppingListModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSubmit={handleCreateList}
      />
    </div>
  );
}
