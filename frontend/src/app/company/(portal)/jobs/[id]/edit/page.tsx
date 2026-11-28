import { notFound } from "next/navigation";

import { JobForm } from "@/components/company/JobForm";
import { getMyCompanyCached } from "@/lib/companyPortal";
import { JobsError, jobsJson, type Job, type SkillType } from "@/lib/jobs";

export default async function EditJobPage({ params }: PageProps<"/company/jobs/[id]/edit">) {
  const result = await getMyCompanyCached();
  if (result.status !== "ok" || !result.company) return null;
  const { id } = await params;
  const [job, skillList] = await Promise.all([
    jobsJson<Job>(`/company/vacancies/${encodeURIComponent(id)}`).catch((error) => {
      if (error instanceof JobsError && (error.status === 404 || error.status === 422)) return null;
      throw error;
    }),
    jobsJson<{ skills: { name: string; skill_type: SkillType }[] }>("/company/skill-list")
      .then((r) => r.skills)
      .catch(() => []),
  ]);
  if (!job) notFound();

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="font-display text-[34px] leading-tight font-semibold sm:text-[36px]">
          Edit <em className="text-[#5b3df5]">{job.title}</em>
        </h1>
        <p className="mt-1 text-[15px] text-[#5a5663]">Changes show to students as soon as you save a published job.</p>
      </div>
      <JobForm job={job} skillList={skillList} companyVerified={result.company.status === "VERIFIED"} />
    </div>
  );
}
