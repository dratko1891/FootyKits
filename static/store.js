document.addEventListener("DOMContentLoaded", function () {
    // Update the total when the page loads
    updateCartTotal();

    // Remove item from the cart
    document.querySelectorAll(".cart-del").forEach(button => {
        button.addEventListener("click", function () {
            const cartRow = this.closest(".cart-row");
            const productId = cartRow.getAttribute('data-product-id'); // Get product ID for removal
            removeFromCart(productId);  // Call the function to remove from cart on the server
            cartRow.remove();  // Remove the row from the DOM
            updateCartTotal();  // Update the cart total
        });
    });

    // Update total price when quantity changes
    document.querySelectorAll(".cart-quantity").forEach(input => {
        input.addEventListener("change", function () {
            if (this.value <= 0) this.value = 1; // Ensure quantity is at least 1
            updateCartTotal();
        });
    });
});

// Function to calculate total price
function updateCartTotal() {
    let total = 0;
    document.querySelectorAll(".cart-row").forEach(row => {
        let quantity = row.querySelector(".cart-quantity").value;
        let price = parseFloat(row.querySelector(".cart-price").textContent.replace(" SEK", "")) || 0;
        total += quantity * price;
    });

    // Display total price
    document.getElementById("cart-total").textContent = "Total: " + total.toFixed(2) + " SEK";
}

// Function to remove an item from the cart on the server side
function removeFromCart(productId) {
    fetch('/remove_from_cart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            product_id: productId,
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log("Product removed successfully");
        } else {
            console.log("Failed to remove product");
        }
    })
    .catch(error => console.error('Error:', error));
}
