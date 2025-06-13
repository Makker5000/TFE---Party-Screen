import { e as ensure_array_like, h as head } from "../../chunks/index.js";
import { e as escape_html } from "../../chunks/escaping.js";
function _page($$payload) {
  let tracks = Array.from({ length: 15 }, (_, i) => ({
    id: i + 1,
    title: `Titre #${i + 1}`,
    votes: 0
  }));
  const each_array = ensure_array_like(tracks);
  head($$payload, ($$payload2) => {
    $$payload2.title = `<title>Vote Music</title>`;
  });
  $$payload.out += `<div class="min-h-screen flex flex-col items-center py-12 px-4"><h1 class="text-5xl font-extrabold mb-8 text-primary">Vote pour ta track préférée</h1> <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 w-full max-w-4xl"><!--[-->`;
  for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
    let track = each_array[$$index];
    $$payload.out += `<div class="card bg-base-100 shadow-lg hover:shadow-xl transition-shadow rounded-2xl"><div class="card-body flex flex-col items-center p-6"><h2 class="text-2xl font-semibold mb-4">${escape_html(track.title)}</h2> <button class="btn btn-accent mb-2 w-32">Voter</button> <span class="text-lg">Votes : ${escape_html(track.votes)}</span></div></div>`;
  }
  $$payload.out += `<!--]--></div></div>`;
}
export {
  _page as default
};
