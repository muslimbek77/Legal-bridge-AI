// src/features/contracts/hooks/useSelection.js
import { useState } from "react";

export default function useSelection(items = []) {
  const [selectedIds, setSelectedIds] = useState([]);

  const isSelected = (id) => selectedIds.includes(id);

  const toggle = (id) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const clear = () => setSelectedIds([]);

  const selectAll = () => {
    setSelectedIds((prev) =>
      prev.length === items.length ? [] : items.map((i) => i.id)
    );
  };

  return {
    selectedIds,
    isSelected,
    toggle,
    selectAll,
    clear,
  };
}