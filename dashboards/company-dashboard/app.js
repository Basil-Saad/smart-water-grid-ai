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

// Get database reference
const db = firebase.database();

console.log("Firebase connected!");

// Consumption values for leak detection
let node1Consumption = 0;
let node2Consumption = 0;
let node3Consumption = 0;

// Leak detection function
function checkLeak() {
  // Avoid division by zero
  if (node1Consumption <= 0) {
    document.getElementById("leak-percent").textContent = "0";
    document.getElementById("leak-message").textContent = "Waiting for data...";
    document.getElementById("leak-section").className = "leak-status no-leak";
    return;
  }
  
  // Calculate leak percentage
  const totalCustomers = node2Consumption + node3Consumption;
  const difference = node1Consumption - totalCustomers;
  const leakPercent = Math.abs((difference / node1Consumption) * 100);
  
  // Update display
  document.getElementById("leak-percent").textContent = leakPercent.toFixed(1);
  
  // Check threshold
  if (leakPercent > 15) {
    document.getElementById("leak-message").textContent = "⚠️ Leak detected!";
    document.getElementById("leak-section").className = "leak-status leak-detected";
  } else {
    document.getElementById("leak-message").textContent = "✓ No leak detected";
    document.getElementById("leak-section").className = "leak-status no-leak";
  }
}

// ----- LISTEN FOR SENSOR DATA -----

// Listen for Node 1 sensor data
db.ref("/nodes/node1/sensors").on("value", function(snapshot) {
  const data = snapshot.val();
  if (data) {
    document.getElementById("node1-consumption").textContent = data.consumption.toFixed(2);
    document.getElementById("node1-level").textContent = data.level.toFixed(1);
    document.getElementById("node1-tds").textContent = data.tds.toFixed(0);
    
    // Store for leak detection
    node1Consumption = data.consumption;
    checkLeak();
  }
});

// Listen for Node 2 sensor data
db.ref("/nodes/node2/sensors").on("value", function(snapshot) {
  const data = snapshot.val();
  if (data) {
    document.getElementById("node2-consumption").textContent = data.consumption.toFixed(2);
    
    // Store for leak detection
    node2Consumption = data.consumption;
    checkLeak();
  }
});

// Listen for Node 3 sensor data
db.ref("/nodes/node3/sensors").on("value", function(snapshot) {
  const data = snapshot.val();
  if (data) {
    document.getElementById("node3-consumption").textContent = data.consumption.toFixed(2);
    
    // Store for leak detection
    node3Consumption = data.consumption;
    checkLeak();
  }
});

// ----- LISTEN FOR ACTUATOR STATES -----

// Node 1 actuators
db.ref("/nodes/node1/actuators").on("value", function(snapshot) {
  const data = snapshot.val();
  if (data) {
    // Update pump button
    const pumpBtn = document.getElementById("node1-pump");
    if (data.pump) {
      pumpBtn.textContent = "Pump: ON";
      pumpBtn.classList.add("on");
    } else {
      pumpBtn.textContent = "Pump: OFF";
      pumpBtn.classList.remove("on");
    }
    
    // Update valve button
    const valveBtn = document.getElementById("node1-valve");
    if (data.valve) {
      valveBtn.textContent = "Valve: OPEN";
      valveBtn.classList.add("on");
    } else {
      valveBtn.textContent = "Valve: CLOSED";
      valveBtn.classList.remove("on");
    }
  }
});

// Node 2 actuators
db.ref("/nodes/node2/actuators").on("value", function(snapshot) {
  const data = snapshot.val();
  if (data) {
    const valveBtn = document.getElementById("node2-valve");
    if (data.valve) {
      valveBtn.textContent = "Valve: OPEN";
      valveBtn.classList.add("on");
    } else {
      valveBtn.textContent = "Valve: CLOSED";
      valveBtn.classList.remove("on");
    }
  }
});

// Node 3 actuators
db.ref("/nodes/node3/actuators").on("value", function(snapshot) {
  const data = snapshot.val();
  if (data) {
    const valveBtn = document.getElementById("node3-valve");
    if (data.valve) {
      valveBtn.textContent = "Valve: OPEN";
      valveBtn.classList.add("on");
    } else {
      valveBtn.textContent = "Valve: CLOSED";
      valveBtn.classList.remove("on");
    }
  }
});

// ----- CONTROL BUTTONS -----

// Node 1 Pump
document.getElementById("node1-pump").addEventListener("click", function() {
  const button = this;
  const currentState = button.classList.contains("on");
  const newState = !currentState;
  
  db.ref("/nodes/node1/actuators/pump").set(newState);
});

// Node 1 Valve
document.getElementById("node1-valve").addEventListener("click", function() {
  const button = this;
  const currentState = button.classList.contains("on");
  const newState = !currentState;
  
  db.ref("/nodes/node1/actuators/valve").set(newState);
});

// Node 2 Valve
document.getElementById("node2-valve").addEventListener("click", function() {
  const button = this;
  const currentState = button.classList.contains("on");
  const newState = !currentState;
  
  db.ref("/nodes/node2/actuators/valve").set(newState);
});

// Node 3 Valve
document.getElementById("node3-valve").addEventListener("click", function() {
  const button = this;
  const currentState = button.classList.contains("on");
  const newState = !currentState;
  
  db.ref("/nodes/node3/actuators/valve").set(newState);
});

// ----- RESET CONSUMPTION BUTTONS -----

document.getElementById("node1-reset").addEventListener("click", function() {
  db.ref("/nodes/node1/commands/resetConsumption").set(true);
});

document.getElementById("node2-reset").addEventListener("click", function() {
  db.ref("/nodes/node2/commands/resetConsumption").set(true);
});

document.getElementById("node3-reset").addEventListener("click", function() {
  db.ref("/nodes/node3/commands/resetConsumption").set(true);
});

// ----- AI DEMAND PREDICTION -----

const PREDICTION_SERVER = 'http://localhost:5000';

// Manual time toggle
document.getElementById('manual-time-toggle').addEventListener('change', function() {
  const selectors = document.getElementById('time-selectors');
  if (this.checked) {
    selectors.classList.remove('hidden');
  } else {
    selectors.classList.add('hidden');
  }
  getPrediction();
});

// Update prediction when time selection changes
document.getElementById('hour-select').addEventListener('change', getPrediction);
document.getElementById('day-select').addEventListener('change', getPrediction);

// Function to get prediction
async function getPrediction() {
  try {
    // Build request body
    const body = {
      consumption: node1Consumption
    };
    
    // Add manual time if enabled
    if (document.getElementById('manual-time-toggle').checked) {
      body.hour = document.getElementById('hour-select').value;
      body.day = document.getElementById('day-select').value;
    }
    
    const response = await fetch(`${PREDICTION_SERVER}/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(body)
    });
    
    const data = await response.json();
    
    if (data.success) {
      document.getElementById('predicted-demand').textContent = data.prediction.toFixed(2);
      
      // Show time info
      let timeText = `${data.time_info.period} (${data.time_info.hour}:00, ${data.time_info.day_name})`;
      if (data.time_info.manual_time) {
        timeText += ' [Manual]';
      }
      document.querySelector('.prediction-info').textContent = timeText;
    } else {
      document.getElementById('predicted-demand').textContent = 'Error';
      console.error('Prediction error:', data.error);
    }
  } catch (error) {
    document.getElementById('predicted-demand').textContent = 'Server offline';
    console.error('Server error:', error);
  }
}

// Refresh prediction button
document.getElementById('refresh-prediction').addEventListener('click', function() {
  getPrediction();
});

// Auto-refresh prediction every 5 seconds
setInterval(getPrediction, 5000);

// Initial prediction after 2 seconds
setTimeout(getPrediction, 2000);