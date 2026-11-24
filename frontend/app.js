const grid = document.querySelector("#product-grid");
const statusEl = document.querySelector("#status");
const cart = new Map();

const money = value => `$${Number(value).toFixed(2)}`;

async function loadProducts() {
  try {
    const response = await fetch("/api/products");
    if (!response.ok) throw new Error("Could not load products");
    const products = await response.json();
    statusEl.textContent = `${products.length} products available`;
    grid.innerHTML = products.map(p => `
      <article class="product-card">
        <img src="${escapeHtml(p.image)}" alt="${escapeHtml(p.name)}" loading="lazy">
        <div class="product-info">
          <h3>${escapeHtml(p.name)}</h3>
          <p>${escapeHtml(p.description)}</p>
          <div class="product-bottom">
            <span class="price">${money(p.price)}</span>
            <button class="add-button" data-id="${p.id}">Add to cart</button>
          </div>
        </div>
      </article>`).join("");
    grid.querySelectorAll(".add-button").forEach(button => {
      button.addEventListener("click", () => addToCart(products.find(p => p.id === Number(button.dataset.id))));
    });
  } catch (error) {
    statusEl.textContent = `${error.message}. Please refresh the page.`;
  }
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, char => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"
  }[char]));
}

function addToCart(product) {
  if (!product) return;
  const current = cart.get(product.id) || {...product, quantity: 0};
  current.quantity += 1;
  cart.set(product.id, current);
  renderCart();
  openCart();
}

function renderCart() {
  const items = [...cart.values()];
  document.querySelector("#cart-count").textContent = items.reduce((sum, p) => sum + p.quantity, 0);
  document.querySelector("#cart-total").textContent = money(items.reduce((sum, p) => sum + p.price * p.quantity, 0));
  document.querySelector("#cart-items").innerHTML = items.length ? items.map(p => `
    <div class="cart-line">
      <div><strong>${escapeHtml(p.name)}</strong><small>${money(p.price)} each</small></div>
      <div class="quantity-controls">
        <button data-action="minus" data-id="${p.id}" aria-label="Decrease quantity">−</button>
        <span>${p.quantity}</span>
        <button data-action="plus" data-id="${p.id}" aria-label="Increase quantity">+</button>
      </div>
    </div>`).join("") : "<p>Your cart is empty.</p>";

  document.querySelectorAll("[data-action]").forEach(button => {
    button.addEventListener("click", () => {
      const id = Number(button.dataset.id);
      const item = cart.get(id);
      if (button.dataset.action === "plus") item.quantity += 1;
      else item.quantity -= 1;
      if (item.quantity <= 0) cart.delete(id);
      renderCart();
    });
  });
}

function openCart() {
  document.querySelector("#cart-panel").classList.add("open");
  document.querySelector("#overlay").classList.add("show");
}
function closeCart() {
  document.querySelector("#cart-panel").classList.remove("open");
  document.querySelector("#overlay").classList.remove("show");
}

document.querySelector("#cart-toggle").addEventListener("click", openCart);
document.querySelector("#cart-close").addEventListener("click", closeCart);
document.querySelector("#overlay").addEventListener("click", closeCart);

document.querySelector("#checkout-form").addEventListener("submit", async event => {
  event.preventDefault();
  const items = [...cart.values()];
  if (!items.length) return alert("Your cart is empty.");
  const customerName = document.querySelector("#customer-name").value.trim();
  try {
    const response = await fetch("/api/orders", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({
        customer_name: customerName,
        items: items.map(item => ({product_id:item.id, quantity:item.quantity}))
      })
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Order failed");
    alert(`Demo order #${result.order_id} created. Total: ${money(result.total)}`);
    cart.clear();
    renderCart();
    closeCart();
    event.target.reset();
    loadOrders();
  } catch (error) {
    alert(error.message);
  }
});

async function loadOrders() {
  const container = document.querySelector("#orders-list");
  try {
    const response = await fetch("/api/orders");
    const orders = await response.json();
    container.innerHTML = orders.length ? orders.map(order => `
      <div class="order-row">
        <span><strong>Order #${order.id}</strong> · ${escapeHtml(order.customer_name)}</span>
        <strong>${money(order.total)}</strong>
      </div>`).join("") : "No orders yet. Place a demo order to see it here.";
  } catch {
    container.textContent = "Unable to load orders.";
  }
}

renderCart();
loadProducts();
loadOrders();
