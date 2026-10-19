"use client";

import { useState } from "react";
import { Briefcase, Clock, FileText } from "lucide-react";

import { CareerReadinessResultModal } from "./CareerReadinessResultModal";
import { type AnalysisHistoryRecord, getAnalysisDetail, RECENT_ANALYSES } from "./mockData";

interface RecentAnalysisHistoryProps {
  onViewDetails?: (item: AnalysisHistoryRecord) => void;
}

// Recent Analysis History table showing past evaluations, score bars, and actions
export function RecentAnalysisHistory({ onViewDetails }: RecentAnalysisHistoryProps = {}) {
  const [selectedRecord, setSelectedRecord] = useState<AnalysisHistoryRecord | null>(null);

  const handleView = (item: AnalysisHistoryRecord) => {
    setSelectedRecord(item);
    if (onViewDetails) {
      onViewDetails(item);
    }
  };

  const activeDetailData = selectedRecord ? getAnalysisDetail(selectedRecord) : null;

  return (
    <>
      <div className="bg-white border-2 border-ink rounded-2xl shadow-[4px_4px_0px_#000] overflow-hidden">
        {/* Lime Header Bar with View All Action */}
        <div className="bg-lime border-b-2 border-ink px-5 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="size-5 text-ink" />
            <h3 className="font-extrabold text-base sm:text-lg text-ink">
              Recent Analysis History
            </h3>
          </div>
          <button
            type="button"
            className="bg-[#edddfc] hover:bg-[#dec2fa] text-ink font-bold text-xs px-4 py-1.5 rounded-lg border-2 border-ink shadow-[2px_2px_0px_#000] transition-all hover:-translate-y-0.5 active:translate-y-0 cursor-pointer"
          >
            View All
          </button>
        </div>

        {/* Responsive Analysis Records Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse min-w-[640px]">
            <thead>
              <tr className="border-b border-ink/10 bg-gray-50/60 text-[11px] font-bold text-muted uppercase tracking-wider">
                <th scope="col" className="px-5 py-3.5 text-left">
                  Role
                </th>
                <th scope="col" className="px-4 py-3.5 text-center">
                  Readiness Score
                </th>
                <th scope="col" className="px-4 py-3.5 text-center">
                  Date
                </th>
                <th scope="col" className="px-5 py-3.5 text-center">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ink/10 text-sm">
              {RECENT_ANALYSES.map((item) => (
                <tr key={item.id} className="hover:bg-cream/40 transition-colors">
                  {/* Role title with career level placed on a separate line beneath */}
                  <td className="px-5 py-4 text-left">
                    <div className="flex items-center gap-3">
                      <span className="size-8 rounded-lg border-2 border-ink bg-white flex items-center justify-center shadow-[1px_1px_0px_#000] shrink-0">
                        <Briefcase className="size-4 text-ink" />
                      </span>
                      <div className="flex flex-col text-left">
                        <span className="font-extrabold text-ink text-sm leading-tight">
                          {item.role}
                        </span>
                        <span className="text-xs text-muted font-semibold mt-0.5 leading-tight">
                          {item.careerLevel}
                        </span>
                      </div>
                    </div>
                  </td>

                  {/* Readiness Score Progress Bar */}
                  <td className="px-4 py-4 text-center">
                    <div className="flex items-center justify-center gap-3">
                      <div className="w-28 sm:w-36 h-3 bg-[#e2e8f0] rounded-full overflow-hidden border border-ink/20">
                        <div
                          className="bg-[#006ee9] h-full rounded-full transition-all duration-500"
                          style={{ width: `${item.readinessScore}%` }}
                        />
                      </div>
                      <span className="text-sm font-black text-[#006ee9] min-w-[2.5rem]">
                        {item.readinessScore}%
                      </span>
                    </div>
                  </td>

                  {/* Persisted Evaluation Timestamp */}
                  <td className="px-4 py-4 text-center text-xs font-medium text-muted whitespace-nowrap">
                    {item.date}
                  </td>

                  {/* Actions: View (opens modal) and Download Report without line wrap */}
                  <td className="px-5 py-4 text-center">
                    <div className="inline-flex items-center justify-center gap-2">
                      <button
                        type="button"
                        onClick={() => handleView(item)}
                        className="bg-[#1e40af] hover:bg-[#1d4ed8] text-white text-[11px] font-bold px-3.5 py-1.5 rounded-lg border-2 border-ink shadow-[2px_2px_0px_#000] hover:-translate-y-0.5 active:translate-y-0 transition-all cursor-pointer whitespace-nowrap"
                      >
                        View
                      </button>
                      <button
                        type="button"
                        className="bg-lime hover:bg-[#c2f37c] text-ink text-[11px] font-bold px-2.5 py-1.5 rounded-lg border-2 border-ink shadow-[2px_2px_0px_#000] hover:-translate-y-0.5 active:translate-y-0 transition-all flex items-center gap-1.5 whitespace-nowrap cursor-pointer shrink-0"
                      >
                        <FileText className="size-3.5 text-ink shrink-0" />
                        <span>Download Report</span>
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Career Readiness Result Modal */}
      <CareerReadinessResultModal
        isOpen={Boolean(selectedRecord)}
        onClose={() => setSelectedRecord(null)}
        data={activeDetailData}
      />
    </>
  );
}
