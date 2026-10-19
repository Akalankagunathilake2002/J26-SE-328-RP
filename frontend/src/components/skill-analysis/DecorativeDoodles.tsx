// Decorative background shapes and playful doodles matching the Skillaro visual identity
export function DecorativeBackground() {
  return (
    <div
      aria-hidden="true"
      className="pointer-events-none fixed inset-0 overflow-hidden z-0 select-none"
    >
      {/* Top Left: Lavender & Yellow Organic Accents */}
      <div className="absolute -top-12 -left-12 w-48 h-64 bg-[#c8a5ff]/40 rounded-full blur-2xl" />
      <div className="absolute top-8 left-4 w-10 h-16 bg-[#ffde4d]/60 rounded-full rotate-45 hidden lg:block" />
      <span className="absolute top-28 left-8 text-sun text-xl hidden lg:block font-bold">
        ✦
      </span>

      {/* Top Right: Playful Blobs and Sparks */}
      <div className="absolute -top-10 -right-10 w-56 h-72 bg-[#c8a5ff]/45 rounded-full blur-2xl" />
      <span className="absolute top-24 right-12 text-[#ffde4d] text-2xl hidden lg:block">
        ✦
      </span>
      <div className="absolute top-44 right-6 w-8 h-20 bg-[#c8a5ff]/50 rounded-full -rotate-12 hidden lg:block" />

      {/* Mid Left: Doodles */}
      <div className="absolute top-1/3 left-4 w-7 h-16 bg-[#ffe03a]/50 rounded-full rotate-12 hidden lg:block" />
      <span className="absolute top-[48%] left-8 text-[#9e80fc] text-xl hidden lg:block">
        ✦
      </span>

      {/* Mid Right: Accents */}
      <div className="absolute top-1/3 -right-6 w-36 h-48 bg-[#c8a5ff]/35 rounded-full blur-xl" />
      <span className="absolute top-[45%] right-8 text-[#ffde4d] text-lg hidden lg:block">
        ✦
      </span>

      {/* Bottom Left & Right Shapes */}
      <div className="absolute -bottom-10 -left-10 w-44 h-44 bg-[#c8a5ff]/40 rounded-full blur-2xl" />
      <div className="absolute -bottom-10 -right-10 w-52 h-52 bg-[#ffe03a]/30 rounded-full blur-2xl" />
    </div>
  );
}
