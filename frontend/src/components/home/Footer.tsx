import Image from "next/image";
import Link from "next/link";

import { FacebookIcon, LinkedInIcon, MailIcon, MapPinIcon, PhoneIcon, TwitterIcon } from "@/components/icons";

// Footer content follows the original design. The links have no pages yet.
const columns = [
  { title: "Home", links: ["Features", "Our Testimonials", "FAQ"] },
  { title: "About Us", links: ["Our Mission", "Our Vision", "Awards and Recognitions", "History", "Teachers"] },
  { title: "Academics", links: ["Special Features", "Gallery"] },
  { title: "Contact Us", links: ["Information", "Map & Direction"] },
];

// A contact with no text yet (the email) isn't shown.
const contacts = [
  { Icon: MailIcon, label: "Email", text: "" },
  { Icon: PhoneIcon, label: "Phone", text: "+91 91813 23 2309" },
  { Icon: MapPinIcon, label: "Location", text: "Somewhere in the World" },
].filter((contact) => contact.text);

const legal = ["Terms of Service", "Privacy Policy", "Cookie Policy"];

const socials = [
  { label: "Facebook", Icon: FacebookIcon, tone: "bg-[#efe8ff] text-[#4a2fd0]" },
  { label: "Twitter", Icon: TwitterIcon, tone: "bg-[#ffdcee] text-[#a3135a]" },
  { label: "LinkedIn", Icon: LinkedInIcon, tone: "bg-[#dbeeff] text-[#0b4a80]" },
];

/** Compact site footer, shared by the home page and the other pages. */
export function Footer() {
  return (
    <footer className="mt-12 border-t border-[#e6e2da] bg-white font-nav text-[#141413]">
      <div className="mx-auto max-w-[1240px] px-4 pb-[18px] pt-8 sm:px-8">
        <div className="flex flex-wrap justify-between gap-7">
          <div className="max-w-[360px] flex-[1_1_280px]">
            <Image
              src="/brand/skillaro-logo.png"
              alt="Skillaro — Align your skills. Shape your career"
              width={120}
              height={41}
              className="h-[41px] w-[120px] object-contain"
            />
            <p className="mt-2 text-sm leading-[1.55] text-[#5c5a55]">
              We believe in the power of play to foster creativity, problem-solving skills, and imagination.
            </p>
            <ul className="mt-3 flex flex-col gap-1.5 text-[13.5px] text-[#3d3b36]">
              {contacts.map(({ Icon, label, text }) => (
                <li key={label} className="flex items-center gap-2">
                  <Icon className="size-[15px] shrink-0 text-[#5b3df5]" />
                  <span className="sr-only">{label}: </span>
                  {text}
                </li>
              ))}
            </ul>
          </div>

          <nav
            aria-label="Footer"
            className="grid flex-[2_1_480px] grid-cols-2 gap-5 sm:grid-cols-[repeat(auto-fit,minmax(110px,1fr))]"
          >
            {columns.map((column) => (
              <div key={column.title}>
                <h2 className="text-sm font-semibold">{column.title}</h2>
                <ul className="mt-2 flex flex-col gap-[5px] text-[13.5px]">
                  {column.links.map((link) => (
                    <li key={link}>
                      <Link href="#" className="text-[#5c5a55] hover:text-[#141413] hover:underline">
                        {link}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </nav>
        </div>

        <div className="mt-[22px] flex flex-wrap items-center justify-between gap-3 border-t border-[#efebe4] pt-3.5 text-[13.5px]">
          <ul className="flex flex-wrap gap-x-[18px] gap-y-1.5">
            {legal.map((item) => (
              <li key={item}>
                <Link href="#" className="text-[#5c5a55] hover:text-[#141413] hover:underline">
                  {item}
                </Link>
              </li>
            ))}
          </ul>
          <ul className="flex gap-2">
            {socials.map(({ label, Icon, tone }) => (
              <li key={label}>
                <Link
                  href="#"
                  aria-label={label}
                  className={`grid size-11 place-items-center rounded-full transition-transform hover:-translate-y-0.5 ${tone}`}
                >
                  <Icon className="size-[17px]" />
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </footer>
  );
}
