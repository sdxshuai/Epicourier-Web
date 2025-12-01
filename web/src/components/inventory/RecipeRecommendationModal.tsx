"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  ChefHat,
  Clock,
  ShoppingCart,
  Sparkles,
  Check,
  X,
  Loader2,
  ExternalLink,
} from "lucide-react";
import type {
  InventoryRecipeRecommendation,
  InventoryRecommendResponse,
} from "@/types/data";

interface RecipeRecommendationModalProps {
  isOpen: boolean;
  onClose: () => void;
  recommendations: InventoryRecommendResponse | null;
  isLoading: boolean;
  onAddToShoppingList?: (missingIngredients: string[]) => void;
}

export function RecipeRecommendationModal({
  isOpen,
  onClose,
  recommendations,
  isLoading,
  onAddToShoppingList,
}: RecipeRecommendationModalProps) {
  const [expandedRecipe, setExpandedRecipe] = useState<number | null>(null);

  const getMatchScoreColor = (score: number) => {
    if (score >= 80) return "bg-green-100 text-green-800 border-green-200";
    if (score >= 50) return "bg-yellow-100 text-yellow-800 border-yellow-200";
    return "bg-red-100 text-red-800 border-red-200";
  };

  const getMatchScoreLabel = (score: number) => {
    if (score >= 80) return "Excellent Match";
    if (score >= 50) return "Good Match";
    return "Partial Match";
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-2xl max-h-[85vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="size-5 text-amber-500" />
            AI Recipe Recommendations
          </DialogTitle>
          <DialogDescription>
            Recipes suggested based on your inventory, prioritizing expiring ingredients
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-12 gap-4">
            <Loader2 className="size-8 animate-spin text-primary" />
            <p className="text-sm text-muted-foreground">
              Analyzing your inventory and finding the best recipes...
            </p>
          </div>
        ) : recommendations ? (
          <ScrollArea className="max-h-[60vh] pr-4">
            {/* Overall Summary */}
            {recommendations.overall_reasoning && (
              <div className="mb-4 p-3 bg-muted/50 rounded-lg">
                <p className="text-sm text-muted-foreground">
                  {recommendations.overall_reasoning}
                </p>
              </div>
            )}

            {/* Recipe Cards */}
            <div className="space-y-4">
              {recommendations.recommendations.map((recipe, index) => (
                <RecipeCard
                  key={recipe.recipe_id}
                  recipe={recipe}
                  index={index}
                  isExpanded={expandedRecipe === recipe.recipe_id}
                  onToggle={() =>
                    setExpandedRecipe(
                      expandedRecipe === recipe.recipe_id ? null : recipe.recipe_id
                    )
                  }
                  onAddToShoppingList={onAddToShoppingList}
                  getMatchScoreColor={getMatchScoreColor}
                  getMatchScoreLabel={getMatchScoreLabel}
                />
              ))}
            </div>

            {/* Shopping Suggestions */}
            {recommendations.shopping_suggestions.length > 0 && (
              <>
                <Separator className="my-4" />
                <div className="p-3 bg-blue-50 dark:bg-blue-950/30 rounded-lg">
                  <h4 className="font-medium text-sm flex items-center gap-2 mb-2">
                    <ShoppingCart className="size-4 text-blue-600" />
                    Shopping Suggestions
                  </h4>
                  <p className="text-xs text-muted-foreground mb-2">
                    Add these ingredients to unlock more recipes:
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {recommendations.shopping_suggestions.map((ingredient) => (
                      <Badge key={ingredient} variant="outline" className="text-xs">
                        {ingredient}
                      </Badge>
                    ))}
                  </div>
                </div>
              </>
            )}
          </ScrollArea>
        ) : (
          <div className="flex flex-col items-center justify-center py-12 gap-4">
            <ChefHat className="size-12 text-muted-foreground/50" />
            <p className="text-sm text-muted-foreground">
              No recommendations available
            </p>
          </div>
        )}

        <div className="flex justify-end pt-2">
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// Separate component for recipe card to keep code organized
interface RecipeCardProps {
  recipe: InventoryRecipeRecommendation;
  index: number;
  isExpanded: boolean;
  onToggle: () => void;
  onAddToShoppingList?: (ingredients: string[]) => void;
  getMatchScoreColor: (score: number) => string;
  getMatchScoreLabel: (score: number) => string;
}

function RecipeCard({
  recipe,
  index,
  isExpanded,
  onToggle,
  onAddToShoppingList,
  getMatchScoreColor,
  getMatchScoreLabel,
}: RecipeCardProps) {
  return (
    <div className="border rounded-lg overflow-hidden">
      {/* Card Header */}
      <button
        onClick={onToggle}
        className="w-full p-4 flex items-start justify-between hover:bg-muted/30 transition-colors text-left"
      >
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-medium text-muted-foreground">
              #{index + 1}
            </span>
            <h3 className="font-semibold">{recipe.recipe_name}</h3>
          </div>
          <p className="text-sm text-muted-foreground line-clamp-2">
            {recipe.reason}
          </p>
        </div>
        <Badge
          variant="outline"
          className={`ml-4 shrink-0 ${getMatchScoreColor(recipe.match_score)}`}
        >
          {recipe.match_score}% {getMatchScoreLabel(recipe.match_score)}
        </Badge>
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="px-4 pb-4 space-y-3 border-t bg-muted/20">
          {/* Expiring Ingredients Used */}
          {recipe.expiring_ingredients_used.length > 0 && (
            <div className="pt-3">
              <h4 className="text-xs font-medium text-amber-600 flex items-center gap-1 mb-1.5">
                <Clock className="size-3" />
                Uses Expiring Ingredients
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {recipe.expiring_ingredients_used.map((ing) => (
                  <Badge
                    key={ing}
                    variant="outline"
                    className="text-xs bg-amber-50 text-amber-700 border-amber-200"
                  >
                    {ing}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Available Ingredients */}
          {recipe.ingredients_available.length > 0 && (
            <div>
              <h4 className="text-xs font-medium text-green-600 flex items-center gap-1 mb-1.5">
                <Check className="size-3" />
                You Have ({recipe.ingredients_available.length})
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {recipe.ingredients_available.map((ing) => (
                  <Badge
                    key={ing}
                    variant="outline"
                    className="text-xs bg-green-50 text-green-700 border-green-200"
                  >
                    {ing}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Missing Ingredients */}
          {recipe.ingredients_missing.length > 0 && (
            <div>
              <h4 className="text-xs font-medium text-red-600 flex items-center gap-1 mb-1.5">
                <X className="size-3" />
                Missing ({recipe.ingredients_missing.length})
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {recipe.ingredients_missing.map((ing) => (
                  <Badge
                    key={ing}
                    variant="outline"
                    className="text-xs bg-red-50 text-red-700 border-red-200"
                  >
                    {ing}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-2 pt-2">
            <Button
              size="sm"
              variant="outline"
              className="text-xs"
              asChild
            >
              <a href={`/dashboard/recipes?id=${recipe.recipe_id}`} target="_blank">
                <ExternalLink className="size-3 mr-1" />
                View Recipe
              </a>
            </Button>
            {recipe.ingredients_missing.length > 0 && onAddToShoppingList && (
              <Button
                size="sm"
                variant="outline"
                className="text-xs"
                onClick={() => onAddToShoppingList(recipe.ingredients_missing)}
              >
                <ShoppingCart className="size-3 mr-1" />
                Add Missing to List
              </Button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default RecipeRecommendationModal;
