const stats = [
  { value: "10K+", label: "Students", detail: "Building their skills", tone: "text-[#5b3df5]" },
  { value: "500+", label: "Companies", detail: "Hiring our students", tone: "text-[#c2410c]" },
  { value: "1.2K+", label: "Job Listings", detail: "Analyzed daily", tone: "text-[#be185d]" },
  { value: "85%", label: "Improvement", detail: "In career readiness", tone: "text-[#15803d]" },
  { value: "4.8/5", label: "Student Rating", detail: "Loved by learners", tone: "text-[#0369a1]" },
];

export function StatsBar() {
  return (
    <section aria-label="Skillaro in numbers" className="mt-10 border-y border-[#e6e2da] bg-white">
      <ul className="mx-auto grid max-w-[1180px] grid-cols-2 gap-x-5 gap-y-4 px-4 py-[18px] sm:flex sm:flex-wrap sm:justify-between sm:gap-x-6 sm:px-8">
        {stats.map(({ value, label, detail, tone }) => (
          <li key={label} className="flex items-center gap-2.5">
            <span className={`font-editorial text-[22px] font-semibold sm:text-[26px] ${tone}`}>{value}</span>
            <span className="leading-tight">
              <span className="block font-bold">{label}</span>
              <span className="block text-[13.5px] text-[#66635c]">{detail}</span>
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
