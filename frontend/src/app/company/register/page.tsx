import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { CompanyRegisterForm } from "@/components/company/CompanyForms";
import { Footer } from "@/components/home/Footer";
import { Navbar } from "@/components/home/Navbar";
import { getCurrentUser } from "@/lib/auth";

export const metadata: Metadata = { title: "Create a company account — Skillaro" };

const STEPS = [
  "Create a company account. A Skillaro admin checks your company once.",
  "Write the job. Skillaro finds the skills in your description, and you mark each one Required or Preferred.",
  "Once your company is verified, students see your jobs on Skillaro's Jobs page and apply there. You see each applicant's name, contact details and CV.",
];

export default async function CompanyRegisterPage() {
  const user = await getCurrentUser();
  if (user) redirect(user.role === "hr" ? "/company" : "/");

  return (
    <div className="min-h-screen bg-[#f4f2ee] text-[#1d1b24]">
      <Navbar currentPath="/company" />
      <section className="mt-5 bg-[#241a5e] px-4 py-12 sm:px-6 lg:py-16">
        <div className="mx-auto flex max-w-[1120px] flex-wrap items-center gap-10">
          <div className="flex min-w-0 flex-[1_1_380px] flex-col gap-5 text-white">
            <span className="self-start rounded-full bg-[#d0ffa4] px-3 py-1 text-xs font-bold text-[#1f3a00]">For employers</span>
            <h1 className="font-display text-[40px] leading-[1.05] font-semibold sm:text-[48px]">
              Find graduates with the <em className="text-[#d0ffa4]">skills you need</em>
            </h1>
            <p className="max-w-[470px] text-[17px] leading-relaxed text-[#ddd8ff]">
              Post your vacancies on Skillaro. Students see exactly which skills you ask for, and can work on the ones they are missing.
            </p>
            <ol className="flex max-w-[470px] flex-col gap-3">
              {STEPS.map((step, i) => (
                <li key={step} className="flex items-start gap-3">
                  <span className="grid size-[30px] shrink-0 place-items-center rounded-full bg-[#d0ffa4] text-[13px] font-extrabold text-[#1f3a00]">{i + 1}</span>
                  <span className="text-[15px] leading-normal text-[#f1efff]">{step}</span>
                </li>
              ))}
            </ol>
          </div>
          <div className="flex min-w-0 max-w-[480px] flex-[1_1_400px] flex-col gap-4 rounded-[18px] bg-white p-6 shadow-[0_30px_60px_-30px_rgba(0,0,0,0.5)] sm:p-7">
            <div>
              <h2 className="font-display text-[28px] font-semibold">
                Create a <em className="text-[#5b3df5]">company</em> account
              </h2>
              <p className="mt-1 text-sm text-[#5a5663]">Your jobs go live after a Skillaro admin checks your company.</p>
            </div>
            <CompanyRegisterForm />
          </div>
        </div>
      </section>
      <Footer />
    </div>
  );
}
