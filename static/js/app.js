document.addEventListener("DOMContentLoaded", () => {
  const flashes = document.querySelectorAll(".flash");
  flashes.forEach((el) => {
    setTimeout(() => {
      el.style.transition = "opacity 0.35s ease, transform 0.35s ease";
      el.style.opacity = "0";
      el.style.transform = "translateY(-6px)";
      setTimeout(() => el.remove(), 400);
    }, 4200);
  });

  const search = document.querySelector('input[type="search"]');
  if (search) {
    search.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        search.value = "";
        search.form?.submit();
      }
    });
  }
});
