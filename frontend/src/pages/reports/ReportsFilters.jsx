// src/pages/reports/ReportsFilters.jsx
import { MagnifyingGlassIcon } from "@heroicons/react/24/outline";

export default function ReportsFilters({
  searchTerm,
  onSearchChange,
  formatFilter,
  onFormatChange,
}) {
  return (
    <div className="card p-4">
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1 relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Hisobot qidirish..."
            value={searchTerm}
            onChange={(e) => onSearchChange(e.target.value)}
            className="input-field pl-10"
          />
        </div>

        <div className="sm:w-48">
          <select
            value={formatFilter}
            onChange={(e) => onFormatChange(e.target.value)}
            className="input-field"
          >
            <option value="">Barcha formatlar</option>
            <option value="pdf">PDF</option>
            <option value="docx">DOCX</option>
            <option value="html">HTML</option>
          </select>
        </div>
      </div>
    </div>
  );
}