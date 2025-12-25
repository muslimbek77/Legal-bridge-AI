import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeftIcon,
  DocumentTextIcon,
  ArrowPathIcon,
  DocumentArrowDownIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  InformationCircleIcon,
  ClockIcon,
  ChevronDownIcon,
  LanguageIcon,
  ArrowTopRightOnSquareIcon,
  ClipboardDocumentIcon,
} from "@heroicons/react/24/outline";
import { format, set } from "date-fns";
import toast from "react-hot-toast";
import LoadingSpinner from "../components/LoadingSpinner";
import ContractStatusBadge from "../components/ContractStatusBadge";
import { RiskScoreCircle } from "../components/RiskScoreBadge";
import ComplianceIssueBadge from "../components/ComplianceIssueBadge";
import contractsService from "../services/contracts";
import analysisService from "../services/analysis";
import reportsService from "../services/reports";
import { Alert, Card, Divider, Tag, Select, Badge } from "antd";
import {
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  FileTextOutlined,
} from "@ant-design/icons";

export default function ContractDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [reportMenuOpen, setReportMenuOpen] = useState(false);
  const [showMatnUz, setShowMatnUz] = useState(false);
  const [textCopied, setTextCopied] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [severityFilter, setSeverityFilter] = useState("all");

  const {
    data: contract,
    isLoading: contractLoading,
    error: contractError,
  } = useQuery({
    queryKey: ["contract", id],
    queryFn: () => contractsService.getContract(id),
    retry: 2,
  });

  const { data: analysisData, refetch: refetchAnalysis } = useQuery({
    queryKey: ["contract-analysis", id],
    queryFn: () => analysisService.getAnalysisByContract(id),
    enabled:
      !!contract &&
      (contract.status === "analyzed" || contract.status === "processing"),
    refetchInterval: contract?.status === "processing" ? 3000 : false,
  });

  // Use real data only - no mock data
  const displayContract = contract;
  const displayAnalysis = analysisData?.results?.[0] || null;

  const analyzeMutation = useMutation({
    mutationFn: () => contractsService.analyzeContract(id),
    onSuccess: () => {
      queryClient.invalidateQueries(["contract", id]);
      queryClient.invalidateQueries(["contract-analysis", id]);
      toast.success("Tahlil boshlandi", { duration: 2200 });
    },
    onError: () => {
      toast.error("Tahlil boshlashda xatolik");
    },
  });

  const generateReportMutation = useMutation({
    mutationFn: (format) => reportsService.generateReport(id, format),
    onSuccess: () => {
      toast.success("Hisobot yaratildi");
      queryClient.invalidateQueries(["reports"]);
    },
    onError: () => {
      toast.error("Hisobot yaratishda xatolik");
    },
  });

  const handleGenerateReport = (format) => {
    generateReportMutation.mutate(format);
    setReportMenuOpen(false);
  };

  // Refetch contract data when analysis is completed
  useEffect(() => {
    if (displayAnalysis?.status === "completed") {
      queryClient.invalidateQueries(["contract", id]);
    }
  }, [displayAnalysis?.status, id, queryClient]);

  if (contractLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }
  // console.log("contract", contract);
  // console.log("displayContract", displayContract);
  // console.log("displayAnalysis", displayAnalysis);
  // console.log("displayAnalysis", displayAnalysis);
  // console.log("analysisData", analysisData?.results);

  if (contractError || !displayContract) {
    return (
      <div className="text-center py-12">
        <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">
          Shartnoma topilmadi
        </h3>
        <p className="mt-1 text-sm text-gray-500">
          So'ralgan shartnoma mavjud emas yoki o'chirilgan.
        </p>
        <p className="mt-1 text-xs text-gray-400">ID: {id}</p>
        <div className="mt-6">
          <Link to="/contracts" className="btn-primary">
            Shartnomalar ro'yxati
          </Link>
        </div>
      </div>
    );
  }

  const getRiskColor = (risk) => {
    switch (risk) {
      case "low":
        return "text-green-600 bg-green-50";
      case "medium":
        return "text-yellow-600 bg-yellow-50";
      case "high":
        return "text-orange-600 bg-orange-50";
      case "critical":
        return "text-red-600 bg-red-50";
      default:
        return "text-gray-600 bg-gray-50";
    }
  };

  const severityConfig = {
    critical: { color: "red", label: "Jiddiy" },
    high: { color: "orange", label: "Yuqori" },
    medium: { color: "gold", label: "O‘rta" },
    low: { color: "green", label: "Past" },
  };

  const issueTypeMap = {
    missing_info: "Yetishmayotgan ma’lumot",
    spelling: "Imloviy xato",
    grammar: "Grammatik xato",
  };

  const uiStatus = displayAnalysis?.status;

  // console.log(displayAnalysis?.status);
  // console.log("uiStatus", uiStatus);
  // console.log("displayAnalysis", displayAnalysis);
  // console.log(displayContract);
  // console.log("uiStatus", uiStatus);

  // console.log("displayContract", displayContract);

  const severityOrder = {
    critical: 4,
    high: 3,
    medium: 2,
    low: 1,
  };

  const sortedIssues = [...(displayAnalysis?.issues || [])].sort(
    (a, b) => severityOrder[b.severity] - severityOrder[a.severity]
  );
  const filteredIssues =
    severityFilter === "all"
      ? sortedIssues
      : sortedIssues.filter((issue) => issue.severity === severityFilter);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <button
            onClick={() => navigate(-1)}
            className="flex items-center text-sm text-gray-500 hover:text-gray-700 mb-4"
          >
            <ArrowLeftIcon className="h-4 w-4 mr-1" />
            Orqaga
          </button>
          <div className="flex items-center gap-4">
            <DocumentTextIcon className="h-10 w-10 text-gray-400" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {displayContract.title}
              </h1>
              <div className="mt-1 flex items-center gap-3">
                <ContractStatusBadge status={uiStatus} />
                <span className="text-sm text-gray-500">
                  {format(
                    new Date(displayContract.created_at),
                    "dd.MM.yyyy HH:mm"
                  )}
                </span>
              </div>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {/* File action buttons */}
          {displayContract.original_file &&
            (() => {
              const fileUrl = displayContract.original_file.toLowerCase();

              if (fileUrl.endsWith(".docx")) {
                return (
                  <a
                    href={displayContract.original_file}
                    download
                    className="btn-secondary cursor-pointer flex items-center"
                  >
                    <DocumentArrowDownIcon className="h-5 w-5 mr-2" />
                    Yuklab olish
                  </a>
                );
              } else {
                return (
                  <a
                    href={displayContract.original_file}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-secondary cursor-pointer flex items-center"
                  >
                    <ArrowTopRightOnSquareIcon className="h-5 w-5 mr-2" />
                    Ko‘rish
                  </a>
                );
              }

              return null;
            })()}

          {uiStatus !== "completed" && (
            <button
              onClick={() => analyzeMutation.mutate()}
              disabled={uiStatus === "in_progress" || analyzeMutation.isPending}
              className={`btn-primary ${
                uiStatus === "in_progress"
                  ? "opacity-60 cursor-not-allowed"
                  : ""
              }`}
            >
              <ArrowPathIcon
                className={`h-5 w-5 mr-2 ${
                  analyzeMutation.isPending ? "animate-spin" : ""
                }`}
              />
              Tahlil qilish
            </button>
          )}

          <div className="relative">
            {uiStatus === "completed" && (
              <button
                onClick={() => setReportMenuOpen(!reportMenuOpen)}
                className="btn-secondary flex items-center"
              >
                <DocumentArrowDownIcon className="h-5 w-5 mr-2" />
                Hisobot
                <ChevronDownIcon className="h-4 w-4 ml-2" />
              </button>
            )}
            {reportMenuOpen && (
              <>
                <div
                  className="fixed inset-0 z-10"
                  onClick={() => setReportMenuOpen(false)}
                />
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg ring-1 ring-black ring-opacity-5 z-20">
                  <div className="py-1">
                    <button
                      onClick={() => handleGenerateReport("pdf")}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      PDF formatda
                    </button>
                    {/* <button
                      onClick={() => handleGenerateReport("docx")}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      DOCX formatda
                    </button> */}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Contract Info & Analysis */}
        <div className="lg:col-span-2 space-y-6">
          {/* Contract Info */}
          <div className="card p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Shartnoma ma'lumotlari
            </h3>
            <dl className="grid grid-cols-2 gap-4">
              <div>
                <dt className="text-sm font-medium text-gray-500">
                  Shartnoma raqami
                </dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {displayContract.contract_number || "-"}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">
                  Shartnoma turi
                </dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {displayContract.contract_type_display ||
                    displayContract.contract_type}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">
                  1-tomon (Buyurtmachi)
                </dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {displayContract.party_a || "-"}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">
                  1-tomon INN
                </dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {displayContract.party_a_inn || "-"}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">
                  2-tomon (Ijrochi)
                </dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {displayContract.party_b || "-"}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">
                  2-tomon INN
                </dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {displayContract.party_b_inn || "-"}
                </dd>
              </div>
              {displayContract.contract_date && (
                <div>
                  <dt className="text-sm font-medium text-gray-500">
                    Shartnoma sanasi
                  </dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {format(
                      new Date(displayContract.contract_date),
                      "dd.MM.yyyy"
                    )}
                  </dd>
                </div>
              )}

              <div>
                <dt className="text-sm font-medium text-gray-500">
                  Shartnoma summasi
                </dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {displayContract.total_amount
                    ? `${Number(displayContract.total_amount).toLocaleString(
                        "fr-FR",
                        {
                          minimumFractionDigits: 0,
                          maximumFractionDigits: 0,
                        }
                      )} ${displayContract.currency}`
                    : "-"}
                </dd>
              </div>

              <div className="col-span-2">
                <dt className="text-sm font-medium text-gray-500">Izoh</dt>
                <dd className="mt-1 text-sm text-gray-900 whitespace-pre-wrap">
                  {displayContract.notes || "-"}
                </dd>
              </div>
              <div className="col-span-2">
                {uiStatus === "completed" && displayAnalysis && (
                  <>
                    <dt className="text-sm font-medium text-gray-500">
                      Shartnoma tili
                    </dt>
                    <dd className="mt-1 text-sm text-gray-900 whitespace-pre-wrap">
                      {displayContract.language_display == "Русский"
                        ? "Rus tili"
                        : displayContract.language_display}
                    </dd>
                  </>
                )}
              </div>
            </dl>
          </div>

          {/* Analysis Summary */}
          {uiStatus === "completed" && displayAnalysis && (
            <>
              <div className="card p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">
                  Tahlil xulosasi
                </h3>
                <div className="mt-2 rounded-lg border border-gray-200 bg-gray-50 p-4 space-y-2">
                  {displayAnalysis.summary.split("\n").map((line, index) => {
                    if (line.startsWith("Shartnoma tahlili yakunlandi")) {
                      return (
                        <p
                          key={index}
                          className="text-sm font-semibold text-gray-900"
                        >
                          {line}
                        </p>
                      );
                    }
                    if (line.startsWith("Til: ru")) {
                      return (
                        <p
                          key={index}
                          className="text-sm font-semibold text-gray-900"
                        >
                          Til: Rus tili
                        </p>
                      );
                    }
                    if (line.startsWith("Til: uz-latn")) {
                      return (
                        <p
                          key={index}
                          className="text-sm font-semibold text-gray-900"
                        >
                          Til: O'zbek tili (Lotin)
                        </p>
                      );
                    }
                    if (line.startsWith("Til: uz-cyrl")) {
                      return (
                        <p
                          key={index}
                          className="text-sm font-semibold text-gray-900"
                        >
                          Til: O'zbek tili (Kiril)
                        </p>
                      );
                    }
                    if (line.startsWith("Aniqlangan muammolar")) {
                      return (
                        <p
                          key={index}
                          className="text-sm font-medium text-gray-800 mt-2"
                        >
                          ⚠️ {line}
                        </p>
                      );
                    }

                    if (line.startsWith("-")) {
                      return (
                        <p
                          key={index}
                          className="text-sm text-gray-700 ml-4 flex items-center gap-2"
                        >
                          <span className="w-1.5 h-1.5 rounded-full bg-gray-400" />
                          {line.replace("-", "").trim()}
                        </p>
                      );
                    }

                    if (line.startsWith("Xavf darajasi")) {
                      // Extract score number from string like: "Xavf darajasi: 78/100 - past (qonunga mos)"
                      const match = line.match(/(\d+)\s*\/\s*100/);
                      const score = match ? Number(match[1]) : null;

                      const colorClass =
                        score !== null && score >= 75
                          ? "text-green-500"
                          : score !== null && score >= 50
                          ? "text-yellow-500"
                          : "text-red-500";

                      return (
                        <p
                          key={index}
                          className={`text-base font-semibold mt-3 ${colorClass}`}
                        >
                          {line}
                        </p>
                      );
                    }

                    return (
                      <p key={index} className="text-sm text-gray-600">
                        {line}
                      </p>
                    );
                  })}
                </div>
                <div className="mt-4 flex items-center text-xs text-gray-500">
                  <ClockIcon className="h-4 w-4 mr-1" />
                  <span>
                    Tahlil vaqti:{" "}
                    {(() => {
                      const t = displayAnalysis.processing_time;
                      if (!t && t !== 0) return "-";

                      if (t < 60) {
                        return `${t.toFixed(1)} soniya`;
                      }

                      if (t < 3600) {
                        return `${(t / 60).toFixed(1)} daqiqa`;
                      }

                      return `${(t / 3600).toFixed(1)} soat`;
                    })()}
                  </span>
                </div>
              </div>

              {/* Matn.uz Imlo Tekshiruvi */}
              {/* {uiStatus === "completed" &&
                displayAnalysis &&
                displayContract.extracted_text && (
                  <div className="card">
                    <div className="card-header flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <LanguageIcon className="h-5 w-5 text-purple-600" />
                        <h3 className="text-lg font-medium text-gray-900">
                          Imlo tekshiruvi (Matn.uz)
                        </h3>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => {
                            if (displayContract.extracted_text) {
                              navigator.clipboard.writeText(
                                displayContract.extracted_text
                              );
                              setTextCopied(true);
                              toast.success("Matn nusxalandi!");
                              setTimeout(() => setTextCopied(false), 2000);
                            }
                          }}
                          className="btn-secondary text-sm flex items-center gap-1"
                          disabled={!displayContract.extracted_text}
                        >
                          <ClipboardDocumentIcon className="h-4 w-4" />
                          {textCopied ? "Nusxalandi!" : "Matnni nusxalash"}
                        </button>
                        <a
                          href="https://matn.uz"
                          target="_blank"
                          rel="noopener noreferrer"
                          className="btn-secondary text-sm flex items-center gap-1"
                        >
                          <ArrowTopRightOnSquareIcon className="h-4 w-4" />
                          Matn.uz ga o'tish
                        </a>
                      </div>
                    </div>
                    <div className="p-4">
                      {showMatnUz && (
                        <div className="border rounded-lg overflow-hidden">
                          <div className="bg-purple-50 p-3 border-b flex items-center justify-between">
                            <span className="text-sm text-purple-700 font-medium">
                              📝 Matn.uz - O'zbek tili imlo tekshiruvchisi
                            </span>
                            <span className="text-xs text-purple-500">
                              Matnni quyidagi maydonga joylang va "Tekshirish"
                              tugmasini bosing
                            </span>
                          </div>
                          <iframe
                            src="https://matn.uz"
                            className="w-full border-0"
                            style={{ height: "600px" }}
                            title="Matn.uz Imlo Tekshiruvi"
                            sandbox="allow-same-origin allow-scripts allow-forms allow-popups"
                          />
                        </div>
                      )}

                      {!showMatnUz && displayContract.extracted_text && (
                        <div className="bg-gray-50 rounded-lg p-4">
                          <h4 className="text-sm font-medium text-gray-700 mb-2">
                            Shartnoma matni:
                          </h4>
                          <div className="max-h-48 overflow-y-auto">
                            <pre className="text-xs text-gray-600 whitespace-pre-wrap font-sans">
                              {displayContract.extracted_text}
                            </pre>
                          </div>
                          <p className="mt-3 text-xs text-green-500">
                            💡 "Matnni nusxalash" tugmasini bosing va Matn.uz
                            saytiga o'tib tekshiring
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                )} */}
            </>
          )}

          {/* Processing status */}
          {uiStatus == "in_progress" && (
            <div className="card p-8 text-center">
              <LoadingSpinner size="lg" className="mb-4" />
              <h3 className="text-lg font-medium text-gray-900">
                Tahlil qilinmoqda...
              </h3>
              <p className="mt-2 text-sm text-gray-500">
                Shartnoma sun'iy intellekt yordamida tahlil qilinmoqda.
                Yuklangan fayl hajmiga qarab tahlil jarayoni o'rtacha 1
                soniyadan 5 daqiqagacha vaqt oladi.
              </p>
            </div>
          )}
        </div>

        {/* Right Column - Risk Score & Sections */}
        <div className="space-y-6">
          {/* Risk Score */}
          {uiStatus === "completed" && displayAnalysis && (
            <div className="card p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4 text-center">
                Risk Bahosi
              </h3>
              <div className="flex justify-center mb-4">
                <RiskScoreCircle
                  score={displayAnalysis.overall_score}
                  size={160}
                />
              </div>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">
                    Aniqlilik darajasi
                  </span>
                  <span className="text-sm font-semibold text-green-600">
                    {displayAnalysis.compliance_score}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-green-500 h-2 rounded-full"
                    style={{ width: `${displayAnalysis.compliance_score}%` }}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Issue Summary */}
          {uiStatus === "completed" && displayAnalysis?.issues && (
            <div className="card p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Muammolar xulosasi
              </h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <ExclamationTriangleIcon className="h-5 w-5 text-red-500 mr-2" />
                    <span className="text-sm text-gray-600">Jiddiy</span>
                  </div>
                  <span className="font-semibold text-red-600">
                    {
                      displayAnalysis.issues.filter(
                        (i) => i.severity === "critical"
                      ).length
                    }
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <ExclamationTriangleIcon className="h-5 w-5 text-orange-500 mr-2" />
                    <span className="text-sm text-gray-600">Yuqori</span>
                  </div>
                  <span className="font-semibold text-orange-600">
                    {
                      displayAnalysis.issues.filter(
                        (i) => i.severity === "high"
                      ).length
                    }
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500 mr-2" />
                    <span className="text-sm text-gray-600">O'rta</span>
                  </div>
                  <span className="font-semibold text-yellow-600">
                    {
                      displayAnalysis.issues.filter(
                        (i) => i.severity === "medium"
                      ).length
                    }
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <InformationCircleIcon className="h-5 w-5 text-blue-500 mr-2" />
                    <span className="text-sm text-gray-600">Ma'lumot</span>
                  </div>
                  <span className="font-semibold text-blue-600">
                    {
                      displayAnalysis.issues.filter(
                        (i) => i.severity === "info"
                      ).length
                    }
                  </span>
                </div>
                {/* Imloviy xatolar */}
                <div className="flex items-center justify-between pt-2 border-t border-gray-200 mt-2">
                  <div className="flex items-center">
                    <LanguageIcon className="h-5 w-5 text-purple-500 mr-2" />
                    <span className="text-sm text-gray-600">
                      Imloviy xatolar
                    </span>
                  </div>
                  <span className="font-semibold text-purple-600">
                    {
                      displayAnalysis.issues.filter(
                        (i) => i.issue_type === "spelling"
                      ).length
                    }
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Sections Analysis */}
          {uiStatus === "completed" && displayAnalysis?.sections && (
            <div className="card p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Bo'limlar tahlili
              </h3>
              <ul className="space-y-2">
                {displayAnalysis.sections.map((section, index) => (
                  <li
                    key={index}
                    className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0"
                  >
                    <span className="text-sm text-gray-700">
                      {section.title}
                    </span>
                    <div className="flex items-center gap-2">
                      {section.issues_count > 0 && (
                        <span className="text-xs text-gray-500">
                          {section.issues_count}
                        </span>
                      )}
                      <span
                        className={`px-2 py-0.5 text-xs rounded ${getRiskColor(
                          section.risk
                        )}`}
                      >
                        {section.risk === "low"
                          ? "Past"
                          : section.risk === "medium"
                          ? "O'rta"
                          : section.risk === "high"
                          ? "Yuqori"
                          : "Kritik"}
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
      {/* Compliance Issues */}
      {displayAnalysis?.issues?.length > 0 && (
        <div className="card ">
          <div className="card-header flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">
              Muvofiqlik muammolari
            </h3>
            <div className="flex items-center gap-3">
              <Select
                value={severityFilter}
                onChange={(value) => setSeverityFilter(value)}
                size="small"
                style={{ width: 160, padding: 3 }}
                options={[
                  { value: "all", label: "Barchasi" },
                  { value: "critical", label: "🔴 Jiddiy" },
                  { value: "high", label: "🟠 Yuqori" },
                  { value: "medium", label: "🟡 O‘rta" },
                  { value: "low", label: "🟢 Past" },
                ]}
              />

              <Badge
                count={filteredIssues.length}
                style={{ backgroundColor: "#1677ff" }}
              />
            </div>
          </div>

          <ul className="space-y-4  bg-gray-50 rounded-xl">
            {filteredIssues.map((issue) => (
              <Card
                key={issue.id}
                variant={false}
                className="mb-4 rounded-none  shadow-sm hover:shadow-md transition-shadow bg-white"
                styles={{ padding: 16 }}
              >
                {/* Header */}
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-center gap-2">
                    <ExclamationCircleOutlined className="text-red-500 text-lg" />
                    <h4 className="text-sm font-bold text-gray-900">
                      {issue.title}
                    </h4>
                  </div>

                  <div className="flex items-center gap-2">
                    <Tag color={severityConfig[issue.severity]?.color}>
                      {severityConfig[issue.severity]?.label}
                    </Tag>
                    <Tag color="blue">
                      {issueTypeMap[issue.issue_type] ||
                        issue.issue_type_display}
                    </Tag>
                  </div>
                </div>

                {/* Description */}
                <p className="mt-2 text-sm font-b text-gray-600">
                  {issue.description}
                </p>

                {/* Section */}
                {(issue.section_reference || issue.clause_reference) && (
                  <div className="mt-2 text-xs text-gray-500">
                    📍 <span className="font-medium">Joylashuv:</span>{" "}
                    {issue.section_reference || issue.clause_reference}
                  </div>
                )}

                {/* Law reference */}
                {(issue.law_name || issue.law_article) && (
                  <Alert
                    className="mt-3 flex items-center py-3"
                    type="info"
                    showIcon
                    icon={<FileTextOutlined />}
                    title="Huquqiy asos"
                    description={`${issue.law_name} ${issue.law_article}`}
                  />
                )}

                {/* Recommendation */}
                {issue.suggestion && (
                  <div className="mt-3 bg-blue-50 border border-blue-100 rounded-lg p-3">
                    <p className="text-sm text-blue-800">
                      <strong>Tavsiya:</strong> {issue.suggestion}
                    </p>
                  </div>
                )}

                {/* Resolution */}
                <Divider className="my-3" />

                <div className="mt-2 flex items-center gap-2">
                  <span className="text-xs text-gray-500 font-medium">
                    Holati:
                  </span>
                  {issue.is_resolved ? (
                    <Tag
                      color="green"
                      className="flex items-center gap-1 px-2 py-0.5 rounded-full"
                    >
                      <CheckCircleOutlined />
                      Hal qilingan
                    </Tag>
                  ) : (
                    <Tag
                      color="red"
                      className="flex items-center gap-1 px-2 py-0.5 rounded-full"
                    >
                      <ClockIcon className="h-3 w-3" />
                      Hal qilinmagan
                    </Tag>
                  )}
                </div>
              </Card>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
