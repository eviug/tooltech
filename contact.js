/* Tooltech Technologies - contact form (email + message, no name field).
   GitHub Pages cannot run PHP, so there is no server to send mail. There are two options:
   1. Default: the visitor's email app opens with the message ready to send to our address.
   2. Optional: paste a free Formspree form address below and the message is sent directly
      (messages then arrive in your inbox without opening an email app).      */
(function () {
  "use strict";

  var TO = "tooltechtechnologies@gmail.com";
  var FORM_ENDPOINT = ""; // example: "https://formspree.io/f/xxxxxxxx"  (leave empty to use the email app)

  var form = document.getElementById("contactForm");
  if (!form) return;
  var note = document.getElementById("contactNote");
  var loadedAt = Date.now();

  function show(type, text) {
    note.className = "form-note " + type;
    note.textContent = text;   // text only, never HTML
    note.hidden = false;
  }
  function noControl(s) { return String(s).replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g, ""); }

  form.addEventListener("submit", function (e) {
    e.preventDefault();

    // bots fill the hidden field or submit instantly: pretend it worked and do nothing
    if (document.getElementById("contactWebsite").value !== "" || Date.now() - loadedAt < 2500) {
      show("ok", "Thank you. Your message has been sent.");
      return;
    }

    var email = document.getElementById("contactEmail").value.trim();
    var message = noControl(document.getElementById("contactMessage").value).replace(/\r\n?/g, "\n").trim();

    if (!/^[^\s@<>()]+@[^\s@<>()]+\.[^\s@<>()]{2,}$/.test(email) || email.length > 120) {
      show("err", "Please enter a valid email address.");
      return;
    }
    if (message.length < 5) { show("err", "Please type a message of at least a few words."); return; }
    if (message.length > 3000) { show("err", "Your message is too long. Please shorten it."); return; }

    if (FORM_ENDPOINT) {
      fetch(FORM_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Accept": "application/json" },
        body: JSON.stringify({ email: email, message: message })
      }).then(function (r) {
        if (!r.ok) throw new Error("failed");
        form.reset();
        show("ok", "Thank you. Your message has been sent and we will reply by email.");
      }).catch(function () {
        show("err", "Sorry, we could not send your message. Please email " + TO + " or use WhatsApp.");
      });
      return;
    }

    // email-app route: every value is URL-encoded, so nothing can add extra mail headers
    var subject = "Message from the Tooltech website";
    var body = "From: " + email + "\n\n" + message;
    window.location.href = "mailto:" + TO + "?subject=" + encodeURIComponent(subject) + "&body=" + encodeURIComponent(body);
    show("ok", "Your email app should now open with your message ready. Press Send there. If nothing opened, email " + TO + " directly.");
  });
})();
