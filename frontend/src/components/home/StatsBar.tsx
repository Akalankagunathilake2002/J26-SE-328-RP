import { BriefcaseIcon, ChartIcon, CheckIcon, StarIcon, UsersIcon } from "@/components/icons";

const stats = [
  { value: "10K+", label: "Students", detail: "Building their skills", Icon: UsersIcon, tone: "bg-pink text-white" },
  { value: "500+", label: "Companies", detail: "Hiring our students", Icon: BriefcaseIcon, tone: "bg-brand-blue text-white" },
  { value: "1.2K+", label: "Job Listings", detail: "Analyzed daily", Icon: ChartIcon, tone: "bg-pink text-white" },
  { value: "85%", label: "Improvement", detail: "In career readiness", Icon: CheckIcon, tone: "bg-lime text-[#5a6b4a]" },
  { value: "4.8/5", label: "Student Rating", detail: "Loved by learners", Icon: StarIcon, tone: "bg-brand-blue text-white" },
];

export function StatsBar() {
  return (
    <section aria-label="Skillaro in numbers">
      <div className="border-b-[3px] border-ink bg-sand">
        <ul className="mx-auto grid max-w-[1335px] grid-cols-2 gap-y-6 px-4 py-6 sm:grid-cols-3 lg:h-[115px] lg:grid-cols-5 lg:px-0 lg:py-0">
          {stats.map(({ value, label, detail, Icon, tone }, i) => (
            <li
              key={label}
              className={`flex items-center gap-[19px] pl-[26px] ${i > 0 ? "lg:border-l-[3px] lg:border-ink" : ""} lg:my-[34px] lg:h-[47px]`}
            >
              <span className={`grid size-[43px] shrink-0 place-items-center rounded-[9px] border-[2.5px] border-ink ${tone}`}>
                <Icon className="size-[22px]" />
              </span>
              <div className="lg:-my-4">
                <p className="text-[29px] font-bold leading-[34px] tracking-[-0.01em]">{value}</p>
                <p className="text-[16.5px] font-bold leading-[22px]">{label}</p>
                <p className="text-[14.5px] leading-[20px] text-muted">{detail}</p>
              </div>
            </li>
          ))}
        </ul>
      </div>
      <div aria-hidden="true" className="scallop-edge" />
    </section>
  );
}
