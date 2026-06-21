"use client";

import { Quote, Star } from "lucide-react";
import { Reveal } from "./Reveal";

const TESTIMONIALS = [
  {
    quote:
      "PHOW flagged a new café two blocks away the week it opened. I adjusted my morning specials before it cost me a single regular.",
    author: "Sarah Chen",
    role: "Owner · Bean & Leaf Coffee",
    initials: "SC",
  },
  {
    quote:
      "The feasibility study talked me out of a corner I'd have signed a five-year lease on. That one 'no' was worth a year of subscriptions.",
    author: "Mateo Alvarez",
    role: "Owner · Casa Mateo",
    initials: "MA",
  },
  {
    quote:
      "The daily brief is the first thing I read with my coffee. It caught my rating slipping and drafted the replies — back to 4.7 in a month.",
    author: "Emily Rodriguez",
    role: "Owner · Sweet Rise Bakery",
    initials: "ER",
  },
];

export function TestimonialsSection() {
  return (
    <section className="px-6 py-20 lg:py-28">
      <div className="mx-auto max-w-[1200px]">
        <Reveal className="max-w-2xl mx-auto text-center">
          <p className="font-mono text-[12px] tracking-[0.12em] text-[#a7a7a7] uppercase">
            Loved by owners
          </p>
          <h2 className="mt-5 text-[32px] sm:text-[40px] font-medium leading-[1.12] tracking-[-0.025em] text-white">
            The watchtower indie owners didn&apos;t know they could afford
          </h2>
        </Reveal>

        <div className="mt-14 grid md:grid-cols-3 gap-5">
          {TESTIMONIALS.map((t, i) => (
            <Reveal key={t.author} delay={i * 110}>
              <figure className="dt-card dt-card-hover h-full p-7 flex flex-col">
                <Quote className="w-7 h-7 text-[#6798ff]/40" />
                <blockquote className="mt-4 flex-1 text-[15px] leading-[1.65] text-white/90">
                  {t.quote}
                </blockquote>
                <div className="mt-6 flex">
                  {[0, 1, 2, 3, 4].map((s) => (
                    <Star key={s} className="w-3.5 h-3.5 fill-[#6798ff] text-[#6798ff]" />
                  ))}
                </div>
                <figcaption className="mt-5 flex items-center gap-3 pt-5 border-t border-[#1a1a1a]">
                  <span className="grid place-items-center w-10 h-10 rounded-full bg-[#1e1e1e] text-[13px] font-medium text-white">
                    {t.initials}
                  </span>
                  <div>
                    <p className="text-[14px] font-medium text-white">{t.author}</p>
                    <p className="text-[12.5px] text-[#7c7c7c]">{t.role}</p>
                  </div>
                </figcaption>
              </figure>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
