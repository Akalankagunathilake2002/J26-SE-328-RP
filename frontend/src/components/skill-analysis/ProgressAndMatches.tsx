import { BarChart3, Clock, Star } from "lucide-react";

// Mid-section dashboard placeholders for readiness trend and top role matches
export function ProgressAndMatches() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
      {/* Left Card: Readiness Progress Trend */}
      <div className="bg-white border-2 border-ink rounded-2xl p-5 shadow-[4px_4px_0px_#000] relative flex flex-col justify-between overflow-hidden min-h-[260px]">
        {/* Card Header */}
        <div>
          <div className="flex items-center gap-2">
            <BarChart3 className="size-5 text-ink" />
            <h3 className="font-extrabold text-base text-ink">Readiness Progress</h3>
          </div>
          <p className="text-xs text-muted mt-0.5 font-medium">
            Score trend over last 6 months
          </p>
        </div>

        {/* Decorative Chart Placeholder */}
        <div className="relative mt-4 pt-2 pb-1">
          {/* Y-axis guide lines and labels */}
          <div className="flex flex-col justify-between h-28 text-[10px] text-muted font-mono select-none">
            <div className="flex items-center gap-2">
              <span className="w-5 text-right">100</span>
              <div className="w-full border-b border-dashed border-gray-200" />
            </div>
            <div className="flex items-center gap-2">
              <span className="w-5 text-right">75</span>
              <div className="w-full border-b border-dashed border-gray-200" />
            </div>
            <div className="flex items-center gap-2">
              <span className="w-5 text-right">50</span>
              <div className="w-full border-b border-dashed border-gray-200" />
            </div>
            <div className="flex items-center gap-2">
              <span className="w-5 text-right">25</span>
              <div className="w-full border-b border-dashed border-gray-200" />
            </div>
          </div>

          {/* Decorative chart bars with dashed trend indicator */}
          <div className="grid grid-cols-6 gap-2 sm:gap-3 pl-7 pr-2 mt-2 items-end h-20">
            <div className="flex flex-col items-center gap-1.5 h-full justify-end">
              <div className="w-full bg-[#bfdbfe] rounded-t-sm h-[35%]" />
              <span className="text-[10px] font-bold text-muted">Mar</span>
            </div>
            <div className="flex flex-col items-center gap-1.5 h-full justify-end">
              <div className="w-full bg-[#bfdbfe] rounded-t-sm h-[48%]" />
              <span className="text-[10px] font-bold text-muted">Apr</span>
            </div>
            <div className="flex flex-col items-center gap-1.5 h-full justify-end">
              <div className="w-full bg-[#bfdbfe] rounded-t-sm h-[55%]" />
              <span className="text-[10px] font-bold text-muted">May</span>
            </div>
            <div className="flex flex-col items-center gap-1.5 h-full justify-end">
              <div className="w-full bg-[#bfdbfe] rounded-t-sm h-[62%]" />
              <span className="text-[10px] font-bold text-muted">Jun</span>
            </div>
            <div className="flex flex-col items-center gap-1.5 h-full justify-end">
              <div className="w-full bg-[#bfdbfe] rounded-t-sm h-[74%]" />
              <span className="text-[10px] font-bold text-muted">Jul</span>
            </div>
            <div className="flex flex-col items-center gap-1.5 h-full justify-end">
              <div className="w-full bg-[#93c5fd] rounded-t-sm h-[88%]" />
              <span className="text-[10px] font-bold text-muted">Aug</span>
            </div>
          </div>
        </div>

        {/* Coming Soon Callout Overlay */}
        <div className="absolute inset-0 flex items-center justify-center p-4 bg-white/40 backdrop-blur-[1px] rounded-2xl pointer-events-none">
          <div className="bg-[#fffbeb] border-2 border-ink rounded-xl px-4 py-3 shadow-[3px_3px_0px_#000] text-center max-w-[240px] pointer-events-auto">
            <div className="flex items-center justify-center gap-1.5 text-ink font-black text-xs tracking-wider">
              <Clock className="size-3.5 shrink-0" />
              <span>COMING SOON</span>
            </div>
            <p className="text-[11px] text-muted font-medium mt-1 leading-snug">
              Your readiness progress chart will be available here.
            </p>
          </div>
        </div>
      </div>

      {/* Right Card: Top Role Matches */}
      <div className="bg-white border-2 border-ink rounded-2xl p-5 shadow-[4px_4px_0px_#000] relative flex flex-col justify-between overflow-hidden min-h-[260px]">
        {/* Card Header with View More control */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Star className="size-5 fill-sun text-ink" />
            <h3 className="font-extrabold text-base text-ink">Top Role Matches</h3>
          </div>
          <button
            type="button"
            className="bg-lime text-ink text-xs font-bold px-3 py-1 rounded-lg border-2 border-ink shadow-[2px_2px_0px_#000] hover:-translate-y-0.5 transition-all cursor-pointer"
          >
            View More
          </button>
        </div>

        {/* Skeleton Rows Placeholder */}
        <div className="flex flex-col gap-3 my-auto py-2">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="flex items-center gap-3">
              <div className="size-6 rounded-full bg-[#dbeafe] border border-ink/20 shrink-0" />
              <div className="flex-1 space-y-1.5">
                <div
                  className="h-2.5 bg-[#e2e8f0] rounded-full"
                  style={{ width: `${80 - i * 12}%` }}
                />
                <div className="h-2 bg-[#f1f5f9] rounded-full w-2/5" />
              </div>
            </div>
          ))}
        </div>

        {/* Coming Soon Callout Overlay */}
        <div className="absolute inset-0 flex items-center justify-center p-4 bg-white/40 backdrop-blur-[1px] rounded-2xl pointer-events-none">
          <div className="bg-[#fffbeb] border-2 border-ink rounded-xl px-4 py-3 shadow-[3px_3px_0px_#000] text-center max-w-[240px] pointer-events-auto">
            <div className="flex items-center justify-center gap-1.5 text-ink font-black text-xs tracking-wider">
              <Clock className="size-3.5 shrink-0" />
              <span>COMING SOON</span>
            </div>
            <p className="text-[11px] text-muted font-medium mt-1 leading-snug">
              Personalized role matches will be available here.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
