export const DEFAULT_REORDER_LEVEL = 10;

// Older items may not have a reorder level configured. Treat those as low
// below 10 units, while continuing to respect any item-specific level.
export const getReorderLevel = (min) => Number(min) > 0 ? Number(min) : DEFAULT_REORDER_LEVEL;
export const getStockStatus = (stock, min) => Number(stock) < getReorderLevel(min) ? "low" : "healthy";
export const getStockFill = (stock, min) => Math.min(100, Math.max(0, Number(stock) / (getReorderLevel(min) * 2.5) * 100));
