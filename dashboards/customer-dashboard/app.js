// Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyDPOtU9TyT1noCwo6fY5cBB-YbrZHKnWFk",
  authDomain: "aquagrid-39dc4.firebaseapp.com",
  databaseURL: "https://aquagrid-39dc4-default-rtdb.europe-west1.firebasedatabase.app",
  projectId: "aquagrid-39dc4",
  storageBucket: "aquagrid-39dc4.firebasestorage.app",
  messagingSenderId: "6896419431",
  appId: "1:6896419431:web:6bc950d19a6fef83cdcac2"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const db = firebase.database();

// Pricing tiers
const TIER1_LIMIT = 1;
const TIER2_LIMIT = 2;
const TIER1_PRICE = 0.5;
const TIER2_PRICE = 1;
const TIER3_PRICE = 1.5;

// Current customer
let currentCustomer = null;
let currentListener = null;

// Calculate bill based on tiered pricing
function calculateBill(consumption) {
  let bill = 0;
  let breakdown = "";
  
  if (consumption <= 0) {
    return { bill: 0, breakdown: "No consumption" };
  }
  
  if (consumption <= TIER1_LIMIT) {
    // All in Tier 1
    bill = consumption * TIER1_PRICE;
    breakdown = `${consumption.toFixed(2)} L × ${TIER1_PRICE} SAR = ${bill.toFixed(2)} SAR`;
  } else if (consumption <= TIER2_LIMIT) {
    // Tier 1 + Tier 2
    const tier1Amount = TIER1_LIMIT;
    const tier2Amount = consumption - TIER1_LIMIT;
    const tier1Cost = tier1Amount * TIER1_PRICE;
    const tier2Cost = tier2Amount * TIER2_PRICE;
    bill = tier1Cost + tier2Cost;
    breakdown = `${tier1Amount} L × ${TIER1_PRICE} SAR + ${tier2Amount.toFixed(2)} L × ${TIER2_PRICE} SAR`;
  } else {
    // Tier 1 + Tier 2 + Tier 3
    const tier1Amount = TIER1_LIMIT;
    const tier2Amount = TIER2_LIMIT - TIER1_LIMIT;
    const tier3Amount = consumption - TIER2_LIMIT;
    const tier1Cost = tier1Amount * TIER1_PRICE;
    const tier2Cost = tier2Amount * TIER2_PRICE;
    const tier3Cost = tier3Amount * TIER3_PRICE;
    bill = tier1Cost + tier2Cost + tier3Cost;
    breakdown = `${tier1Amount} L × ${TIER1_PRICE} + ${tier2Amount} L × ${TIER2_PRICE} + ${tier3Amount.toFixed(2)} L × ${TIER3_PRICE}`;
  }
  
  return { bill, breakdown };
}

// Show customer dashboard
function showDashboard(customerNumber) {
  currentCustomer = customerNumber;
  
  // Update UI
  document.getElementById("selection-screen").classList.add("hidden");
  document.getElementById("customer-dashboard").classList.remove("hidden");
  document.getElementById("customer-name").textContent = "Customer " + customerNumber;
  
  // Determine which node to listen to
  const nodePath = customerNumber === 1 ? "/nodes/node2/sensors" : "/nodes/node3/sensors";
  
  // Remove previous listener if exists
  if (currentListener) {
    db.ref(currentListener).off();
  }
  
  // Listen for consumption data
  currentListener = nodePath;
  db.ref(nodePath).on("value", function(snapshot) {
    const data = snapshot.val();
    if (data && data.consumption !== undefined) {
      const consumption = data.consumption;
      const { bill, breakdown } = calculateBill(consumption);
      
      document.getElementById("consumption").textContent = consumption.toFixed(2);
      document.getElementById("bill").textContent = bill.toFixed(2);
      document.getElementById("bill-breakdown").textContent = breakdown;
    }
  });
}

// Show selection screen
function showSelection() {
  // Remove listener
  if (currentListener) {
    db.ref(currentListener).off();
    currentListener = null;
  }
  currentCustomer = null;
  
  // Update UI
  document.getElementById("customer-dashboard").classList.add("hidden");
  document.getElementById("selection-screen").classList.remove("hidden");
}

// Event listeners
document.getElementById("select-customer1").addEventListener("click", function() {
  showDashboard(1);
});

document.getElementById("select-customer2").addEventListener("click", function() {
  showDashboard(2);
});

document.getElementById("back-button").addEventListener("click", function() {
  showSelection();
});