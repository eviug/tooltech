/* PRODUCTS */
      const products = [
        {
          id: "tt-01",
          name: "OTG Type C",
          price: 2000,
          category: "otg",
          image: "img/otg.jpg",
          description: "Remax USB 2.0 Type C",
        },

        {
          id: "tt-02",
          name: "OTG Micro USB",
          price: 2000,
          category: "otg",
          image: "img/otg.jpg",
          description: "Remax USB 2.0 Micro USB",
        },

        {
          id: "tt-03",
          name: "Memory Card 2GB",
          price: 10000,
          category: "memory",
          image: "img/memory-card-2GB.jpg",
          description: "Boost High Speed",
        },

        {
          id: "tt-04",
          name: "Memory Card 4GB",
          price: 15000,
          category: "memory",
          image: "img/memory-card-4GB.jpg",
          description: "Boost High Speed",
        },

        {
          id: "tt-05",
          name: "Memory Card 8GB",
          price: 18000,
          category: "memory",
          image: "img/memory-card-8GB.jpg",
          description: "Boost High Speed",
        },

        {
          id: "tt-06",
          name: "Flash Disk 4GB",
          price: 13500,
          category: "flash",
          image: "img/flash-disk-4GB.jpg",
          description: "Sandisk Ultra Luxe",
        },

        {
          id: "tt-07",
          name: "Flash Disk 8GB",
          price: 15000,
          category: "flash",
          image: "img/flash-disk-8GB.jpg",
          description: "Sandisk Cruzer Blade",
        },

        {
          id: "tt-08",
          name: "Lightning Cable",
          price: 7000,
          category: "cable",
          image: "img/iphone-cable.jpg",
          description: "Lightning To USB",
        },

        {
          id: "tt-09",
          name: "Type C Cable",
          price: 12000,
          category: "cable",
          image: "img/type-c.webp",
          description: "Oraimo Ultra Durable",
        },

        {
          id: "tt-010",
          name: "Micro USB Cable",
          price: 6000,
          category: "cable",
          image: "img/usb-micro-usb.jpg",
          description: "Oraimo Ultra Durable",
        },

        {
          id: "tt-011",
          name: "Oraimo Earphones",
          price: 10000,
          category: "audio",
          image: "img/oraimo-earphones.jpg",
          description: "Deep Bass With Mic",
        },
      ];

      const offers = [products[0], products[1]];
      const coming = [products[2], products[3]];

      /* STATE */
      let activeTab = null;

      /* RENDER MAIN GRID */
      function renderMain() {
        document.getElementById("productGrid").innerHTML = products
          .map(
            (p) => `
<div class="card" onclick="openModal('${p.id}')">

<img src="${p.image}">

<div class="card-content">
<h3>${p.name}</h3>
<p>${p.description}</p>
<div class="price">UGX ${p.price}</div>

<div class="actions">
<button class="wish" onclick="event.stopPropagation();whatsappChat('${p.name}')">💬 chat</button>
<button class="cart" onclick="event.stopPropagation();callNow()">📞 Call</button>
</div>

<div style="display:flex;gap:5px;margin-top:10px;">
<input type="number" min="1" value="1" id="qty-${p.id}" style="width:70px;padding:8px;border:none;border-radius:5px;" onclick="event.stopPropagation();">
<button style="flex:1;padding:10px;background:#F900FE;color:white;border:none;border-radius:5px;cursor:pointer;" onclick="event.stopPropagation();addToCart('${p.id}')">🛒 Cart</button>
</div>

</div>
</div>
`,
          )
          .join("");
      }

      /* TAB CONTENT */
      function showTab(type) {
        const box = document.getElementById("tabContent");

        if (activeTab === type) {
          box.innerHTML = "Click a tab to view featured items";
          activeTab = null;
          return;
        }

        activeTab = type;

        let items = type === "offers" ? offers : coming;

        box.innerHTML = `
<div class="product-grid">
${items
  .map(
    (p) => `
<div class="card" onclick="openModal('${p.id}')">
<img src="${p.image}">
<div class="card-content">
<h3>${p.name}</h3>
<p>${p.description}</p>
<div class="price">UGX ${p.price}</div>
</div>
</div>
`,
  )
  .join("")}
</div>
`;
      }

     

      /* MODAL */
      function openModal(id) {
        let p = products.find((x) => x.id === id);
        document.getElementById("mImg").src = p.image;
        document.getElementById("mName").innerText = p.name;
        document.getElementById("mDesc").innerText = p.description;
        document.getElementById("mPrice").innerText = "UGX " + p.price;
        document.getElementById("modal").style.display = "flex";
      }

      function closeModal() {
        document.getElementById("modal").style.display = "none";
      }

      /* INIT */
      renderMain();
      const navbar = document.getElementById("navbar");
    const navLinks = document.getElementById("navLinks");
    const hamburger = document.getElementById("hamburger");
    const links = document.querySelectorAll(".nav-links a");
    const sections = document.querySelectorAll("section");

    function toggleMenu() {
        navLinks.classList.toggle("show");
        hamburger.classList.toggle("active");
    }

    // Sticky navbar
    window.addEventListener("scroll", () => {
        if (window.scrollY > 50) {
            navbar.classList.add("sticky");
        } else {
            navbar.classList.remove("sticky");
        }

        // Scroll spy
        let current = "";

        sections.forEach(section => {
            const sectionTop = section.offsetTop - 100;
            const sectionHeight = section.clientHeight;

            if (scrollY >= sectionTop && scrollY < sectionTop + sectionHeight) {
                current = section.getAttribute("id");
            }
        });

        links.forEach(link => {
            link.classList.remove("active");
            if (link.getAttribute("href") === "#" + current) {
                link.classList.add("active");
            }
        });
    });

    // Click behavior
    links.forEach(link => {
        link.addEventListener("click", function () {
            links.forEach(l => l.classList.remove("active"));
            this.classList.add("active");

            navLinks.classList.remove("show");
            hamburger.classList.remove("active");
        });
    });
function whatsappChat(productName) {
    const phone = "256741003162";
    const message = encodeURIComponent(
        `Hello Tooltech Technologies, I am interested in ${productName}.`
    );

    window.open(
        `https://wa.me/${phone}?text=${message}`,
        "_blank"
    );
}

function callNow() {
    window.location.href = "tel:+256741003162";
}
    
let cart = [];

function addToCart(productId){
 const product = products.find(p=>p.id===productId);
 const qty = parseInt(document.getElementById(`qty-${productId}`).value)||1;
 const existing = cart.find(i=>i.id===productId);

 if(existing){ existing.qty += qty; }
 else { cart.push({id:product.id,name:product.name,price:product.price,qty:qty}); }

 updateCart();
}

function updateCart(){
 document.getElementById('cartCount').innerText =
 cart.reduce((t,i)=>t+i.qty,0);

 let html='';
 cart.forEach(item=>{
   html += `<div style="padding:10px;border-bottom:1px solid #444;"><strong>${item.name}</strong><br>Qty: ${item.qty}<br>UGX ${(item.price*item.qty).toLocaleString()}</div>`;
 });

 document.getElementById('cartItems').innerHTML = html || '<p>Your cart is empty.</p>';
}

function openCart(){ document.getElementById('cartModal').style.display='flex'; }
function closeCart(){ document.getElementById('cartModal').style.display='none'; }

function sendCartWhatsApp(){
 let text='Hello Tooltech Technologies,%0A%0AI would like to order:%0A';
 cart.forEach(item=>{ text += `• ${item.name} x ${item.qty}%0A`; });
 window.open(`https://wa.me/256741003162?text=${text}`,'_blank');
}