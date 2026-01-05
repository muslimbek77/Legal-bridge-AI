import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  DocumentTextIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  DocumentPlusIcon,
} from "@heroicons/react/24/outline";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import LoadingSpinner from "../components/LoadingSpinner";
import { RiskScoreCircle } from "../components/RiskScoreBadge";
import contractsService from "../services/contracts";
import ContractStatusBadge from "../components/ContractStatusBadge";

const RISK_COLORS = ["#10B981", "#F59E0B", "#F97316", "#EF4444"];

export default function DashboardPage() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ["contract-statistics"],
    queryFn: contractsService.getStatistics,
  });

  // console.log("stats", stats);

  // Haqiqiy ma'lumotlar - agar shartnomalar bo'lmasa, bo'sh ko'rsatiladi
  const hasData = stats?.total > 0;

  // Bo'sh holatdagi ma'lumotlar
  const emptyChartData = {
    contracts_by_type: [],
    monthly_analysis: [
      { month: "Yan", count: 0 },
      { month: "Fev", count: 0 },
      { month: "Mar", count: 0 },
      { month: "Apr", count: 0 },
      { month: "May", count: 0 },
      { month: "Iyun", count: 0 },
    ],
    risk_distribution: [
      { name: "Past (0-25)", value: 0, color: "#10B981" },
      { name: "O'rta (25-50)", value: 0, color: "#F59E0B" },
      { name: "Yuqori (50-75)", value: 0, color: "#F97316" },
      { name: "Kritik (75-100)", value: 0, color: "#EF4444" },
    ],
    recent_contracts: [],
  };

  // Map backend stats to display format
  const displayStats = {
    total_contracts: stats?.total || 0,
    analyzed_contracts: stats?.by_status?.analyzed || 0,
    pending_contracts:
      (stats?.by_status?.uploaded || 0) + (stats?.by_status?.processing || 0),
    critical_issues: stats?.critical_issues || 0,
    average_risk_score: stats?.average_risk_score || 0,
    compliance_rate: stats?.compliance_rate || 0,
    // Haqiqiy ma'lumotlarni ishlatish
    contracts_by_type:
      stats?.by_type?.length > 0
        ? stats.by_type
        : emptyChartData.contracts_by_type,
    monthly_analysis:
      stats?.monthly_analysis?.length > 0
        ? stats.monthly_analysis
        : emptyChartData.monthly_analysis,
    risk_distribution:
      stats?.risk_distribution?.length > 0
        ? stats.risk_distribution
        : emptyChartData.risk_distribution,
    recent_contracts:
      stats?.recent_contracts?.length > 0
        ? stats.recent_contracts
        : emptyChartData.recent_contracts,
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  const statCards = [
    {
      name: "Jami shartnomalar",
      value: displayStats.total_contracts,
      icon: DocumentTextIcon,
      color: "bg-blue-500",
    },
    {
      name: "Tahlil qilingan",
      value: displayStats.analyzed_contracts,
      icon: CheckCircleIcon,
      color: "bg-green-500",
    },
    {
      name: "Kutilmoqda",
      value: displayStats.pending_contracts,
      icon: ClockIcon,
      color: "bg-yellow-500",
    },
    {
      name: "Kritik muammolar",
      value: displayStats.critical_issues,
      icon: ExclamationTriangleIcon,
      color: "bg-red-500",
    },
  ];
  // console.log("displayStats", displayStats);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold text-gray-900">Bosh sahifa</h1>
          <p className="mt-1 text-sm text-gray-500">
            Shartnomalar tahlili umumiy ko‘rinishi
          </p>
        </div>
        <Link
          to="/contracts/upload"
          className="inline-flex items-center gap-2 rounded-xl
  bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white
  shadow-md shadow-indigo-600/30
  hover:bg-indigo-700 hover:shadow-lg transition"
        >
          <DocumentTextIcon className="h-5 w-5" />
          Yangi shartnoma
        </Link>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {statCards.map((stat) => (
          <div key={stat.name} className="card p-5">
            <div className="flex items-center">
              <div className={`flex-shrink-0 rounded-md p-3 ${stat.color}`}>
                <stat.icon className="h-6 w-6 text-white" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    {stat.name}
                  </dt>
                  <dd className="flex items-baseline">
                    <div className="text-2xl font-semibold text-gray-900">
                      {stat.value}
                    </div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Average Risk Score */}
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            O'rtacha Risk Ball
          </h3>
          <div className="flex flex-col items-center">
            <RiskScoreCircle
              score={displayStats.average_risk_score}
              size={150}
            />
            <p className="mt-4 text-sm text-gray-500">
              Muvofiqlik darajasi:{" "}
              <span className="font-semibold text-green-600">
                {displayStats.compliance_rate}%
              </span>
            </p>
          </div>
        </div>

        {/* Risk Distribution Pie Chart */}
        <div className="card p-6 ">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Risk Taqsimoti
          </h3>
          {/* Risk Distribution Pie Chart */}
          {displayStats.risk_distribution.every((item) => item.value === 0) ? (
            <div className="flex flex-col items-center justify-center h-[200px] text-gray-400">
              <ExclamationTriangleIcon className="h-12 w-12 mb-2" />
              <p className="text-sm">Risk ma’lumotlari hali mavjud emas</p>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={displayStats.risk_distribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {displayStats.risk_distribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          )}
          <div className="flex flex-wrap justify-center gap-2 mt-2">
            {displayStats.risk_distribution.map((item) => (
              <div key={item.name} className="flex items-center text-xs">
                <div
                  className="w-3 h-3 rounded-full mr-1"
                  style={{ backgroundColor: item.color }}
                />
                {item.name}
              </div>
            ))}
          </div>
        </div>

        {/* Monthly Analysis Bar Chart */}
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Oylik Tahlillar
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={displayStats.monthly_analysis}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#3B82F6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Bottom row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Shartnoma Turlari */}
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Shartnoma Turlari
          </h3>
          {displayStats.contracts_by_type.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  className=""
                  data={displayStats.contracts_by_type}
                  cx="50%"
                  cy="50%"
                  outerRadius={130}
                  dataKey="value"
                  // label={({ name, percent }) =>
                  //   `${name} (${(percent * 100).toFixed(0)}%)`
                  // }
                >
                  {displayStats.contracts_by_type.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={RISK_COLORS[index % RISK_COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex flex-col items-center justify-center h-[250px] text-gray-400">
              <ChartBarIcon className="h-16 w-16 mb-3" />
              <p className="text-sm">Hali shartnomalar yo'q</p>
            </div>
          )}
          <div className="my-5">
            {displayStats.contracts_by_type.map((item, index) => (
              <div key={item.name} className="flex items-center text-sm mb-2">
                <div
                  className="w-4 h-4 rounded-full mr-2"
                  style={{
                    backgroundColor: RISK_COLORS[index % RISK_COLORS.length],
                  }}
                />
                <span className="mr-2">{item.name}</span>
                <span className="font-semibold text-gray-900">
                  {item.value && `${item.value} ta`}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Contracts */}
        <div className="card">
          <div className="card-header flex items-center justify-between">
            <h3 className="text-lg font-medium text-gray-900">
              So'nggi Shartnomalar
            </h3>
            <Link
              to="/contracts"
              className="text-sm text-primary-600 hover:text-primary-700"
            >
              Barchasini ko'rish →
            </Link>
          </div>
          {displayStats.recent_contracts.length > 0 ? (
            <ul className="divide-y divide-gray-200">
              {displayStats.recent_contracts.map((contract) => (
                <li key={contract.id} className="px-6 py-4 hover:bg-gray-50">
                  <Link
                    to={`/contracts/${contract.id}`}
                    className="flex items-center justify-between"
                  >
                    <div className="flex items-center">
                      <DocumentTextIcon className="h-10 w-10 text-gray-400" />
                      <div className="ml-4 flex flex-col space-y-1">
                        <p className="text-sm font-medium pl-2 text-gray-900">
                          {contract.title}
                        </p>
                        <p className="text-sm text-gray-500 capitalize">
                          {ContractStatusBadge({ status: contract.status })}
                        </p>
                      </div>
                    </div>
                    {contract.risk_score !== null && (
                      <div
                        className={`px-3 py-1 rounded-full text-sm font-semibold ${
                          contract.risk_score < 25
                            ? "bg-green-100 text-green-800"
                            : contract.risk_score < 50
                            ? "bg-yellow-100 text-yellow-800"
                            : contract.risk_score < 75
                            ? "bg-orange-100 text-orange-800"
                            : "bg-red-100 text-red-800"
                        }`}
                      >
                        {contract.risk_score}
                      </div>
                    )}
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-gray-400">
              <DocumentPlusIcon className="h-16 w-16 mb-3" />
              <p className="text-sm mb-4">Hali shartnomalar yuklanmagan</p>
              <Link to="/contracts/upload" className="btn-primary text-sm">
                Birinchi shartnomani yuklash
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
