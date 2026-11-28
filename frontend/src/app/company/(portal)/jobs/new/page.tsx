import { JobForm } from "@/components/company/JobForm";
import { getMyCompanyCached } from "@/lib/companyPortal";
import { jobsJson, type SkillType } from "@/lib/jobs";

export default async function PostJobPage() {
  const result = await getMyCompanyCached();
  if (result.status !== "ok" || !result.company) return null;
  const skillList = await jobsJson<{ skills: { name: string; skill_type: SkillType }[] }>("/company/skill-list")
    .then((r) => r.skills)
    .catch(() => []);

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="font-display text-[34px] leading-tight font-semibold sm:text-[36px]">
          Post a <em className="text-[#5b3df5]">job</em>
        </h1>
        <p className="mt-1 text-[15px] text-[#5a5663]">Fill in the job, then let Skillaro find the skills in your description.</p>
      </div>
      <JobForm skillList={skillList} companyVerified={result.company.status === "VERIFIED"} />
    </div>
  );
}
