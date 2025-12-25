export const getRiskScoreStyles = (score) => {
  if (score == null) return "";

  if (score >= 75) {
    return "text-emerald-700 border-emerald-300 hover:bg-emerald-400";
  }

  if (score >= 50) {
    return "text-yellow-700 border-yellow-300 hover:bg-yellow-400";
  }

  return "text-red-700 border-red-300 hover:bg-red-400";
};