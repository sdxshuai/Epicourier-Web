// Performance optimization for dashboard
// Issue #105: Dashboard loading optimization

import { lazy } from "react";

// Lazy load heavy components
const InventoryPage = lazy(() => import("./inventory/page"));
const ShoppingPage = lazy(() => import("./shopping/page"));
const RecommenderPage = lazy(() => import("./recommender/page"));

// Loading fallback
const LoadingFallback = () => (
  <div className="flex h-screen items-center justify-center">
    <div className="border-primary h-12 w-12 animate-spin rounded-full border-b-2"></div>
  </div>
);

export const dashboardModules = {
  inventory: { Component: InventoryPage, fallback: LoadingFallback },
  shopping: { Component: ShoppingPage, fallback: LoadingFallback },
  recommender: { Component: RecommenderPage, fallback: LoadingFallback },
};
