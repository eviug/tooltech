/* Tooltech Technologies - shop page: filters and the shopping cart.
   The cart lives in the visitor's browser and is sent to us as a WhatsApp message.
   Nothing from a product name, a form field or the URL is ever put into the page as HTML:
   elements are built with textContent, so injected markup cannot run. */
(function () {
  "use strict";

  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  /* ---------- product data (written into the page by build.py) ---------- */
  var dataEl = $("#productData");
  if (!dataEl) return;
  var DATA;
  try { DATA = JSON.parse(dataEl.textContent); } catch (err) { return; }
  var products = DATA.products || {};
  var whatsapp = /^[0-9]{6,15}$/.test(String(DATA.whatsapp)) ? String(DATA.whatsapp) : "";
  var place = typeof DATA.place === "string" ? DATA.place : "";

  /* ---------- filters and search (done in the browser) ---------- */
  var SORTS = ["featured", "low", "high", "name"];
  var DEALS = ["all", "offer", "soon"];
  var state = { q: "", cat: "all", price: "all", deal: "all", sort: "featured" };

  function readUrl() {
    var p = new URLSearchParams(window.location.search);
    // every value is checked against a whitelist; anything else is ignored
    var q = (p.get("q") || "").replace(/[\u0000-\u001F\u007F]+/g, " ").trim().slice(0, 60);
    var cat = p.get("cat"), price = p.get("price"), deal = p.get("deal"), sort = p.get("sort");
    state.q = q;
    state.cat = cat && Object.prototype.hasOwnProperty.call(DATA.categories, cat) ? cat : "all";
    state.price = price && Object.prototype.hasOwnProperty.call(DATA.ranges, price) ? price : "all";
    state.deal = DEALS.indexOf(deal) > -1 ? deal : "all";
    state.sort = SORTS.indexOf(sort) > -1 ? sort : "featured";
  }
  function writeUrl() {
    var p = new URLSearchParams();
    if (state.q) p.set("q", state.q);
    if (state.cat !== "all") p.set("cat", state.cat);
    if (state.price !== "all") p.set("price", state.price);
    if (state.deal !== "all") p.set("deal", state.deal);
    if (state.sort !== "featured") p.set("sort", state.sort);
    var qs = p.toString();
    try { history.replaceState(null, "", window.location.pathname + (qs ? "?" + qs : "") + window.location.hash); } catch (err) {}
  }
  function syncControls() {
    ["cat", "price", "deal"].forEach(function (name) {
      $$('input[name="' + name + '"]').forEach(function (r) { r.checked = r.value === state[name]; });
    });
    var sort = $("#sort"); if (sort) sort.value = state.sort;
    var sq = $("#storeQ"); if (sq) sq.value = state.q;
    var sc = $("#storeCat"); if (sc) sc.value = state.cat;
  }
  function isFiltered() { return !!state.q || state.cat !== "all" || state.price !== "all" || state.deal !== "all"; }

  function applyFilters() {
    var grid = $("#shopGrid");
    if (!grid) return;
    var range = DATA.ranges[state.price] || [0, null];
    var needle = state.q.toLowerCase();
    var ids = Object.keys(products).filter(function (id) {
      var p = products[id];
      if (state.cat !== "all" && p.cat !== state.cat) return false;
      if (p.price < range[0] || (range[1] !== null && p.price > range[1])) return false;
      if (state.deal === "offer" && !p.offer) return false;
      if (state.deal === "soon" && !p.coming) return false;
      if (needle) {
        var hay = (p.name + " " + p.desc + " " + (DATA.categories[p.cat] || "")).toLowerCase();
        if (hay.indexOf(needle) === -1) return false;
      }
      return true;
    });
    ids.sort(function (a, b) {
      var x = products[a], y = products[b];
      if (state.sort === "low") return x.price - y.price;
      if (state.sort === "high") return y.price - x.price;
      if (state.sort === "name") return x.name.localeCompare(y.name);
      return x.order - y.order;
    });
    var shown = {};
    ids.forEach(function (id) { shown[id] = true; });
    // show matching cards in order, hide the rest
    ids.forEach(function (id) {
      var card = document.getElementById("p-" + id);
      if (card) { card.hidden = false; grid.appendChild(card); }
    });
    Object.keys(products).forEach(function (id) {
      if (!shown[id]) { var card = document.getElementById("p-" + id); if (card) card.hidden = true; }
    });

    var label = ids.length + (ids.length === 1 ? " result" : " results");
    if (state.q) label += ' for "' + state.q + '"';
    else if (state.cat !== "all") label += " in " + DATA.categories[state.cat];
    $("#resultCount").textContent = label;   // textContent: never parsed as HTML
    $("#noResults").hidden = ids.length > 0;
    grid.hidden = ids.length === 0;
    $("#clearFilters").hidden = !isFiltered();
    syncControls();
    writeUrl();
  }
  function clearAll() { state = { q: "", cat: "all", price: "all", deal: "all", sort: "featured" }; applyFilters(); }

  var filterForm = $("#filterForm");
  if (filterForm) {
    filterForm.addEventListener("submit", function (e) { e.preventDefault(); });
    filterForm.addEventListener("change", function (e) {
      var t = e.target;
      if (!t) return;
      if (t.type === "radio" && t.name in state) state[t.name] = t.value;
      else if (t.id === "sort") state.sort = SORTS.indexOf(t.value) > -1 ? t.value : "featured";
      else return;
      applyFilters();
    });
  }
  var storeBar = $("#storeBar");
  if (storeBar) {
    storeBar.addEventListener("submit", function (e) {
      e.preventDefault();
      state.q = $("#storeQ").value.replace(/[\u0000-\u001F\u007F]+/g, " ").trim().slice(0, 60);
      var c = $("#storeCat").value;
      state.cat = Object.prototype.hasOwnProperty.call(DATA.categories, c) ? c : "all";
      applyFilters();
    });
  }
  var clearBtn = $("#clearFilters"); if (clearBtn) clearBtn.addEventListener("click", clearAll);
  var clearBtn2 = $("#noResultsClear"); if (clearBtn2) clearBtn2.addEventListener("click", clearAll);
  var filterToggle = $("#filterToggle");
  var filterBody = $("#filterBody");
  if (filterToggle && filterBody) {
    filterToggle.addEventListener("click", function () {
      var open = filterBody.classList.toggle("open");
      filterToggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  /* ---------- helpers ---------- */
  function money(n) { return "UGX " + Number(n).toLocaleString("en-US"); }
  function noControl(s) { return String(s).replace(/[\u0000-\u001F\u007F]+/g, " ").trim(); }

  // Build an element safely: text always goes in as text, never as HTML.
  function el(tag, attrs, kids) {
    var node = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) {
      if (k === "text") node.textContent = attrs[k];
      else node.setAttribute(k, attrs[k]);
    });
    (kids || []).forEach(function (kid) { node.appendChild(typeof kid === "string" ? document.createTextNode(kid) : kid); });
    return node;
  }

  /* ---------- cart state ---------- */
  var KEY = "tooltech_cart";
  var cart = {}; // { productId: quantity }

  function has(id) { return Object.prototype.hasOwnProperty.call(products, id); }

  function loadCart() {
    var out = {};
    try {
      var saved = JSON.parse(localStorage.getItem(KEY)) || [];
      if (Array.isArray(saved)) {
        saved.forEach(function (i) {
          if (!i || typeof i.id !== "string" || !has(i.id) || products[i.id].coming) return;
          var q = parseInt(i.qty, 10);
          if (!(q > 0)) q = 1;
          out[i.id] = Math.min(99, (out[i.id] || 0) + q);
        });
      }
    } catch (err) {}
    return out;
  }
  function saveCart() {
    try {
      localStorage.setItem(KEY, JSON.stringify(Object.keys(cart).map(function (id) { return { id: id, qty: cart[id] }; })));
    } catch (err) {}
  }
  function count() { return Object.keys(cart).reduce(function (n, id) { return n + cart[id]; }, 0); }
  function total() { return Object.keys(cart).reduce(function (t, id) { return t + cart[id] * products[id].price; }, 0); }

  function setQty(id, qty) {
    if (!has(id) || products[id].coming) return;
    qty = Math.max(0, Math.min(99, qty));
    if (qty === 0) delete cart[id]; else cart[id] = qty;
    saveCart();
    refresh();
  }

  /* ---------- drawer ---------- */
  var drawer = $("#cartDrawer");
  var overlay = $("#cartOverlay");
  var cartBtn = $("#cartBtn");
  var lastFocus = null;

  function openDrawer() {
    if (!drawer) return;
    lastFocus = document.activeElement;
    drawer.classList.add("open");
    drawer.setAttribute("aria-hidden", "false");
    overlay.hidden = false;
    document.body.classList.add("no-scroll");
    if (cartBtn) cartBtn.setAttribute("aria-expanded", "true");
    drawer.focus();
  }
  function closeDrawer() {
    if (!drawer) return;
    drawer.classList.remove("open");
    drawer.setAttribute("aria-hidden", "true");
    overlay.hidden = true;
    document.body.classList.remove("no-scroll");
    if (cartBtn) cartBtn.setAttribute("aria-expanded", "false");
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }
  if (cartBtn) cartBtn.addEventListener("click", openDrawer);
  if (overlay) overlay.addEventListener("click", closeDrawer);
  var closeBtn = $("#cartClose");
  if (closeBtn) closeBtn.addEventListener("click", closeDrawer);
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && drawer && drawer.classList.contains("open")) closeDrawer();
  });

  /* ---------- toast ---------- */
  var toastTimer;
  function toast(name) {
    var t = $("#toast");
    if (!t) {
      t = el("div", { id: "toast", role: "status", "aria-live": "polite" });
      document.body.appendChild(t);
    }
    while (t.firstChild) t.removeChild(t.firstChild);
    var view = el("button", { type: "button", "class": "toast-link", text: "View cart" });
    view.addEventListener("click", function () { t.classList.remove("show"); openDrawer(); });
    t.appendChild(el("strong", { text: name }));
    t.appendChild(document.createTextNode(" added to your cart. "));
    t.appendChild(view);
    t.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { t.classList.remove("show"); }, 4000);
  }

  /* ---------- the add button / quantity stepper on each product card ---------- */
  function actionNode(id) {
    var q = cart[id] || 0;
    var name = products[id].name;
    if (!q) return el("button", { type: "button", "class": "btn-add", "data-act": "add", text: "Add to cart" });
    return el("div", { "class": "stepper", role: "group", "aria-label": "Quantity of " + name + " in cart" }, [
      el("button", { type: "button", "data-act": "dec", "aria-label": "Remove one " + name, text: q === 1 ? "\uD83D\uDDD1" : "\u2212" }),
      el("span", {}, [el("b", { text: String(q) }), " in cart"]),
      el("button", { type: "button", "data-act": "inc", "aria-label": "Add one " + name, text: "+" })
    ]);
  }
  function refreshCards() {
    $$(".card-action[data-id]").forEach(function (holder) {
      var id = holder.getAttribute("data-id");
      if (!has(id) || products[id].coming) return;
      while (holder.firstChild) holder.removeChild(holder.firstChild);
      holder.appendChild(actionNode(id));
    });
  }

  /* ---------- the cart list inside the drawer ---------- */
  function renderDrawer() {
    var ids = Object.keys(cart);
    var empty = ids.length === 0;
    $("#cartEmpty").hidden = !empty;
    $("#cartBody").hidden = empty;
    if (empty) return;

    var list = $("#cartItems");
    while (list.firstChild) list.removeChild(list.firstChild);

    ids.forEach(function (id) {
      var p = products[id];
      var q = cart[id];
      var img = el("img", { src: p.image, alt: p.name, "data-fallback": "img/placeholder.svg" });
      var minus = el("button", { type: "button", "data-act": "dec", "aria-label": "Remove one " + p.name, text: "\u2212" });
      if (q === 1) minus.disabled = true;
      var row = el("article", { "class": "cart-row", "data-id": id }, [
        el("a", { "class": "cart-img", href: p.url, tabindex: "-1", "aria-hidden": "true" }, [img]),
        el("div", { "class": "cart-info" }, [
          el("a", { "class": "p-title", href: p.url, text: p.name }),
          el("p", { "class": "unit", text: money(p.price) + " each" }),
          el("div", { "class": "cart-ctrl" }, [
            el("div", { "class": "stepper", role: "group", "aria-label": "Quantity of " + p.name }, [
              minus,
              el("span", {}, [el("b", { text: String(q) })]),
              el("button", { type: "button", "data-act": "inc", "aria-label": "Add one " + p.name, text: "+" })
            ]),
            el("button", { type: "button", "class": "link-del", "data-act": "remove", text: "Delete" })
          ])
        ]),
        el("div", { "class": "line-total", text: money(p.price * q) })
      ]);
      list.appendChild(row);
    });

    var items = count();
    $("#sumLabel").textContent = "Subtotal (" + items + (items === 1 ? " item)" : " items)");
    $("#sumTotal").textContent = money(total());
  }

  function refresh() {
    var c = $("#cartCount");
    if (c) c.textContent = String(count());
    refreshCards();
    renderDrawer();
  }

  /* one click handler for every add / plus / minus / delete button */
  document.addEventListener("click", function (e) {
    var b = e.target.closest ? e.target.closest("[data-act]") : null;
    if (!b) return;
    var holder = b.closest("[data-id]");
    if (!holder) return;
    var id = holder.getAttribute("data-id");
    if (!has(id)) return;
    var act = b.getAttribute("data-act");
    if (act === "add") { setQty(id, (cart[id] || 0) + 1); toast(products[id].name); }
    else if (act === "inc") setQty(id, (cart[id] || 0) + 1);
    else if (act === "dec") setQty(id, (cart[id] || 0) - 1);
    else if (act === "remove") setQty(id, 0);
  });

  window.addEventListener("storage", function (e) {
    if (e.key === KEY) { cart = loadCart(); refresh(); }
  });

  /* ---------- checkout: builds the WhatsApp message ---------- */
  var form = $("#checkoutForm");
  var proceed = $("#proceed");
  var errBox = $("#formError");

  if (form && proceed) {
    proceed.addEventListener("click", function () {
      form.hidden = false;
      proceed.hidden = true;
      $("#cName").focus();
    });
    $("#backToCart").addEventListener("click", function () {
      form.hidden = true;
      proceed.hidden = false;
    });
    $$('input[name="method"]').forEach(function (r) {
      r.addEventListener("change", function () {
        var delivery = $('input[name="method"]:checked').value === "delivery";
        $("#addrWrap").hidden = !delivery;
      });
    });

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (!Object.keys(cart).length) return;

      var name = noControl($("#cName").value).slice(0, 80);
      var phone = noControl($("#cPhone").value).slice(0, 20);
      var delivery = $('input[name="method"]:checked').value === "delivery";
      var addr = noControl($("#cAddr").value).slice(0, 120);
      var notes = noControl($("#cNotes").value).slice(0, 300);

      var problem = "";
      if (!name || !phone || (delivery && !addr)) {
        problem = "Please fill in your name, phone number" + (delivery ? " and delivery location." : ".");
      } else if (!/^[0-9+()\s\-]{7,20}$/.test(phone)) {
        problem = "Please enter a valid phone number.";
      }
      if (problem) {
        errBox.textContent = problem;
        errBox.hidden = false;
        return;
      }
      errBox.hidden = true;
      if (!whatsapp) {
        errBox.textContent = "Ordering is not available right now. Please call us.";
        errBox.hidden = false;
        return;
      }

      var ref = "TT-" + Date.now().toString(36).slice(-5).toUpperCase();
      var lines = Object.keys(cart).map(function (id, i) {
        return (i + 1) + ". " + products[id].name + " x " + cart[id] + " (" + money(products[id].price * cart[id]) + ")";
      });
      var text =
        "Hello Tooltech Technologies, I would like to place an order.\nOrder ref: " + ref + "\n\n" +
        lines.join("\n") +
        "\n\nSubtotal: " + money(total()) + "\n\nName: " + name + "\nPhone: " + phone + "\n" +
        (delivery ? "Delivery to: " + addr + "\n" : "Pick up at Tooltech, " + place + "\n") +
        (notes ? "Notes: " + notes + "\n" : "") +
        "\nPlease confirm availability, delivery cost and how to pay.";

      window.open("https://wa.me/" + whatsapp + "?text=" + encodeURIComponent(text), "_blank", "noopener");
      form.hidden = true;
      $("#sentRef").textContent = ref;
      $("#sent").hidden = false;
    });

    $("#clearCart").addEventListener("click", function () {
      cart = {};
      saveCart();
      $("#sent").hidden = true;
      proceed.hidden = false;
      refresh();
    });
    $("#editOrder").addEventListener("click", function () {
      $("#sent").hidden = true;
      proceed.hidden = false;
    });
  }

  /* ---------- start ---------- */
  readUrl();
  applyFilters();
  cart = loadCart();
  refresh();
})();
