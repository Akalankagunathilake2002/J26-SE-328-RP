import Image from "next/image";
import Link from "next/link";

import { FacebookIcon, LinkedInIcon, MailIcon, MapPinIcon, PhoneIcon, TwitterIcon } from "@/components/icons";

// Footer content follows the design. The links have no pages yet.
const columns = [
  { title: "Home", links: ["Features", "Our Testimonials", "FAQ"] },
  { title: "About Us", links: ["Our Mission", "Our Vision", "Awards and Recognitions", "History", "Teachers"] },
  { title: "Academics", links: ["Special Features", "Gallery"] },
  { title: "Contact Us", links: ["Information", "Map & Direction"] },
];

const contacts = [
  { Icon: MailIcon, label: "Email", text: "" },
  { Icon: PhoneIcon, label: "Phone", text: "+91 91813 23 2309" },
  { Icon: MapPinIcon, label: "Location", text: "Somewhere in the World" },
];

const legal = ["Terms of Service", "Privacy Policy", "Cookie Policy"];

const socials = [
  { label: "Facebook", Icon: FacebookIcon },
  { label: "Twitter", Icon: TwitterIcon },
  { label: "LinkedIn", Icon: LinkedInIcon },
];

export function Footer() {
  return (
    <footer className="mt-24 rounded-t-[16px] lg:mt-[191px] border-x-2 border-t-2 border-ink bg-periwinkle font-nav text-white">
      <div className="mx-auto max-w-[1440px] px-6 pb-[70px] pt-[93px] lg:px-[113px]">
        <div className="flex flex-col gap-12 lg:flex-row lg:justify-between">
          <div>
            <Image
              src="/brand/skillaro-logo.png"
              alt="Skillaro — Align your skills. Shape your career"
              width={147}
              height={50}
              className="-ml-[6px] bg-white"
            />
            <p className="mt-[20px] max-w-[460px] text-[19px] leading-[30.5px]">
              We believe in the power of play to foster creativity, problem-solving skills, and
              imagination.
            </p>
            <ul className="mt-[48px] flex flex-col gap-[22px]">
              {contacts.map(({ Icon, label, text }) => (
                <li key={label} className="flex items-center gap-[10px] text-[19px]">
                  <span className="grid size-[42px] place-items-center rounded-[6px] border-2 border-[#5f6189] bg-[#dbe3ff] text-lime">
                    <Icon className="size-[24px]" />
                  </span>
                  <span className="sr-only">{label}: </span>
                  {text}
                </li>
              ))}
            </ul>
          </div>

          <nav aria-label="Footer" className="grid grid-cols-2 gap-x-6 gap-y-10 sm:grid-cols-4 lg:grid-cols-[repeat(4,128px)] lg:gap-x-[33.5px]">
            {columns.map((column) => (
              <div key={column.title}>
                <h2 className="text-[20px] font-medium">{column.title}</h2>
                <ul className="mt-[23px] flex flex-col gap-[14px] text-[19px] leading-[30px]">
                  {column.links.map((link) => (
                    <li key={link}>
                      <Link href="#" className="hover:underline">
                        {link}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </nav>
        </div>

        <div className="mt-[56px] flex flex-col gap-6 border-y border-ink py-[29px] sm:flex-row sm:items-center sm:justify-between">
          <ul className="flex flex-wrap items-center text-[19px]">
            {legal.map((item, i) => (
              <li key={item} className={i > 0 ? "border-l-2 border-white pl-[22px] ml-[22px]" : ""}>
                <Link href="#" className="hover:underline">
                  {item}
                </Link>
              </li>
            ))}
          </ul>
          <ul className="flex gap-[10px]">
            {socials.map(({ label, Icon }) => (
              <li key={label}>
                <Link
                  href="#"
                  aria-label={label}
                  className="grid size-[58px] place-items-center rounded-[8px] border-2 border-white bg-lime text-white"
                >
                  <Icon className="size-[30px]" />
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </footer>
  );
}
