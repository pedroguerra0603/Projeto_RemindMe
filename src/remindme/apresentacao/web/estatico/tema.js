// Botão de tema claro/escuro. A escolha fica guardada no navegador; sem escolha, vale o tema do sistema.
(function () {
  var raiz = document.documentElement;
  try {
    var salvo = localStorage.getItem("tema");
    if (salvo) raiz.dataset.tema = salvo;
  } catch (e) {}

  document.addEventListener("DOMContentLoaded", function () {
    var botao = document.getElementById("trocar-tema");
    if (!botao) return;
    botao.hidden = false;
    botao.addEventListener("click", function () {
      var escuro = raiz.dataset.tema
        ? raiz.dataset.tema === "escuro"
        : window.matchMedia("(prefers-color-scheme: dark)").matches;
      raiz.dataset.tema = escuro ? "claro" : "escuro";
      try {
        localStorage.setItem("tema", raiz.dataset.tema);
      } catch (e) {}
    });
  });
})();
