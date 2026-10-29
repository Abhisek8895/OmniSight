// OmniSight Mock Store - JavaScript

const products = [
    { id: 1, name: "Wireless Headphones", price: 2499, cat: "audio", icon: "🎧" },
    { id: 2, name: "Smart Watch", price: 3299, cat: "wearables", icon: "⌚" },
    { id: 3, name: "Bluetooth Speaker", price: 1799, cat: "audio", icon: "🔊" },
    { id: 4, name: "Fitness Band", price: 1999, cat: "wearables", icon: "💪" },
    { id: 5, name: "True Wireless Earbuds", price: 2199, cat: "audio", icon: "🎵" },
    { id: 6, name: "Power Bank 20000mAh", price: 1499, cat: "accessories", icon: "🔋" }
];

const FREE_SHIPPING = 5000;
let cart = [];
let category = "all";

const $ = selector => document.querySelector(selector);
const money = n => "₹" + n.toLocaleString("en-IN");

// ---------- Toast ----------
let toastTimer;
function toast(message) {
    const el = $("#toast");
    el.textContent = message;
    el.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.classList.remove("show"), 1800);
}

// ---------- Hero lens follows the cursor ----------
$("#home").addEventListener("pointermove", e => {
    const r = e.currentTarget.getBoundingClientRect();
    e.currentTarget.style.setProperty("--x", (e.clientX - r.left) + "px");
    e.currentTarget.style.setProperty("--y", (e.clientY - r.top) + "px");
});

// ---------- Products: search, filter, sort ----------
function renderProducts() {
    const query = $("#search").value.trim().toLowerCase();
    const sort = $("#sort").value;

    let list = products.filter(p =>
        (category === "all" || p.cat === category) &&
        p.name.toLowerCase().includes(query)
    );
    if (sort === "low") list.sort((a, b) => a.price - b.price);
    if (sort === "high") list.sort((a, b) => b.price - a.price);

    $("#product-grid").innerHTML = list.map(p => `
        <article data-id="${p.id}">
            <span class="icon" aria-hidden="true">${p.icon}</span>
            <h3>${p.name}</h3>
            <p>Price: ${money(p.price)}</p>
            <button type="button">Add to Cart</button>
        </article>
    `).join("");
    $("#no-results").hidden = list.length > 0;
}

$("#search").addEventListener("input", renderProducts);
$("#sort").addEventListener("change", renderProducts);
$("#chips").addEventListener("click", e => {
    const chip = e.target.closest(".chip");
    if (!chip) return;
    category = chip.dataset.cat;
    document.querySelectorAll(".chip").forEach(c => c.classList.toggle("active", c === chip));
    renderProducts();
});

// Add to cart (event delegation, works after every re-render)
$("#product-grid").addEventListener("click", e => {
    const button = e.target.closest("button");
    if (!button) return;
    const product = products.find(p => p.id === Number(button.closest("article").dataset.id));
    const item = cart.find(i => i.id === product.id);
    if (item) item.quantity++;
    else cart.push({ ...product, quantity: 1 });

    renderCart();
    toast(product.name + " added to cart");
    button.textContent = "Added!";
    button.classList.add("added");
    setTimeout(() => { button.textContent = "Add to Cart"; button.classList.remove("added"); }, 1200);
});

// ---------- Cart ----------
function cartTotal() {
    return cart.reduce((sum, i) => sum + i.price * i.quantity, 0);
}

function renderCart() {
    const section = $("#cart");
    const count = cart.reduce((n, i) => n + i.quantity, 0);
    const badge = $("#cart-count");
    badge.textContent = count;
    badge.classList.remove("bump");
    void badge.offsetWidth;
    if (count > 0) badge.classList.add("bump");

    renderSummary();

    if (cart.length === 0) {
        section.innerHTML = `
            <h2>Shopping Cart</h2>
            <p>Your cart is empty. Add a product above to get started.</p>
        `;
        return;
    }

    const total = cartTotal();
    const left = FREE_SHIPPING - total;
    const pct = Math.min(100, Math.round(total / FREE_SHIPPING * 100));

    const itemsHTML = cart.map(item => `
        <div class="cart-item" data-id="${item.id}">
            <h3>${item.icon} ${item.name}</h3>
            <p>Price: ${money(item.price)}</p>
            <p>Subtotal: ${money(item.price * item.quantity)}</p>
            <div class="cart-actions">
                <button type="button" data-act="dec" aria-label="Decrease quantity">-</button>
                <span class="qty">${item.quantity}</span>
                <button type="button" data-act="inc" aria-label="Increase quantity">+</button>
                <button type="button" data-act="remove" class="remove">Remove</button>
            </div>
        </div>
    `).join("");

    section.innerHTML = `
        <h2>Shopping Cart</h2>
        ${itemsHTML}
        <p class="ship">${left > 0 ? `Add ${money(left)} more for free delivery` : "You've unlocked free delivery!"}</p>
        <div class="bar"><span style="width:${pct}%"></span></div>
        <h3 class="total">Total: ${money(total)}</h3>
        <button id="checkout-button" type="button">Proceed to Checkout</button>
    `;
}

$("#cart").addEventListener("click", e => {
    const button = e.target.closest("button");
    if (!button) return;

    if (button.id === "checkout-button") {
        $("#checkout").scrollIntoView({ behavior: "smooth" });
        return;
    }
    const row = button.closest(".cart-item");
    if (!row) return;
    const id = Number(row.dataset.id);
    const act = button.dataset.act;

    if (act === "inc") changeQuantity(id, 1);
    if (act === "dec") changeQuantity(id, -1);
    if (act === "remove") removeProduct(id);
});

function changeQuantity(id, amount) {
    const item = cart.find(i => i.id === id);
    if (!item) return;
    item.quantity += amount;
    if (item.quantity <= 0) return removeProduct(id);
    renderCart();
}

function removeProduct(id) {
    const item = cart.find(i => i.id === id);
    cart = cart.filter(i => i.id !== id);
    renderCart();
    if (item) toast(item.name + " removed");
}

// ---------- Live order summary beside the form ----------
function renderSummary() {
    const box = $("#summary");
    if (cart.length === 0) {
        box.innerHTML = `<h3>Order summary</h3><p>Nothing here yet. Add a product to see your order.</p>`;
        return;
    }
    box.innerHTML = `
        <h3>Order summary</h3>
        <ul>${cart.map(i => `<li><span>${i.name} × ${i.quantity}</span><span>${money(i.price * i.quantity)}</span></li>`).join("")}</ul>
        <div class="sum-total"><span>Total</span><span>${money(cartTotal())}</span></div>
    `;
}

// ---------- Checkout form with live validation ----------
const rules = {
    name: v => v.trim().length >= 2 ? "" : "Enter your full name.",
    email: v => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) ? "" : "Enter a valid email, like name@example.com.",
    address: v => v.trim().length >= 8 ? "" : "Enter your full delivery address."
};

function validateField(id, show = true) {
    const input = $("#" + id);
    const message = rules[id](input.value);
    if (show) {
        input.classList.toggle("invalid", !!message);
        input.classList.toggle("valid", !message);
        document.querySelector(`.error[data-for="${id}"]`).textContent = message;
    }
    return !message;
}

Object.keys(rules).forEach(id => {
    const input = $("#" + id);
    input.addEventListener("blur", () => validateField(id));
    input.addEventListener("input", () => {
        if (input.classList.contains("invalid") || input.classList.contains("valid")) validateField(id);
    });
});

$("#checkout-form").addEventListener("submit", event => {
    event.preventDefault();
    const form = event.target;

    if (cart.length === 0) {
        toast("Add a product to your cart before checkout.");
        $("#products").scrollIntoView({ behavior: "smooth" });
        return;
    }

    const results = Object.keys(rules).map(id => validateField(id));
    if (results.includes(false)) {
        form.classList.remove("shake");
        void form.offsetWidth;
        form.classList.add("shake");
        const firstBad = Object.keys(rules).find(id => $("#" + id).classList.contains("invalid"));
        $("#" + firstBad).focus();
        return;
    }

    const name = $("#name").value.trim();
    const total = cartTotal();
    const orderId = "OS-" + Math.floor(100000 + Math.random() * 900000);

    $("#confirmation").innerHTML = `
        <svg class="tick" viewBox="0 0 64 64" aria-hidden="true"><circle cx="32" cy="32" r="28"/><path d="M20 33l8 8 17-18"/></svg>
        <h2>Order Placed Successfully!</h2>
        <p>Thank you, ${escapeHTML(name)}!</p>
        <p class="order-id">${orderId}</p>
        <p>Your demo order of ${money(total)} has been confirmed.</p>
        <button type="button" id="new-order">Start a new order</button>
    `;

    cart = [];
    renderCart();
    $("#checkout").hidden = true;
    $("#confirmation").scrollIntoView({ behavior: "smooth" });
    form.reset();
    form.querySelectorAll(".valid, .invalid").forEach(el => el.classList.remove("valid", "invalid"));
});

$("#confirmation").addEventListener("click", e => {
    if (e.target.id !== "new-order") return;
    $("#checkout").hidden = false;
    $("#confirmation").innerHTML = `
        <h2>Order Confirmation</h2>
        <p>Your order confirmation message will appear here.</p>
    `;
    $("#products").scrollIntoView({ behavior: "smooth" });
});

// Escape user-provided text before displaying it as HTML
function escapeHTML(value) {
    return value.replace(/[&<>"']/g, c => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    })[c]);
}

// ---------- Highlight the nav link of the section in view ----------
const navLinks = document.querySelectorAll("nav a");
const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            navLinks.forEach(a => a.classList.toggle("active", a.getAttribute("href") === "#" + entry.target.id));
        }
    });
}, { rootMargin: "-40% 0px -55% 0px" });
["home", "products", "cart", "checkout"].forEach(id => observer.observe($("#" + id)));

// ---------- Start ----------
renderProducts();
renderCart();
