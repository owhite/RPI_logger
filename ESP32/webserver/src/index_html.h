
    #ifndef INDEX_HTML_H
    #define INDEX_HTML_H

    #include <pgmspace.h>

    const char index_html[] PROGMEM = R"rawliteral(
    <!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MESC Web Cal</title>
    <style>
      /* Existing styles... */
      body {
          font-family: Arial, sans-serif;
      }
      .tab-container {
          width: 360px;
          align-items: center;
          width: 100%;
      }
      .tab-buttons {
          width: 360px;
          gap: 10px;
          margin-bottom: 10px;
      }
      .tab-content {
          display: none;
          width: 100%;
      }
      .tab-content.active {
          display: block;
      }
      #container1, #container2 {
          width: 360px;
          background-color: #fff;
          padding: 20px;
          box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
      }
      #messages {
          background-color: #fff;
          border: 1px solid #ccc;
          padding: 10px;
          height: 400px;
          overflow-y: scroll;
          word-wrap: break-word;
      }
      .message {
          padding: 5px;
          border-bottom: 1px solid #ddd;
          word-wrap: break-word;
          white-space: pre-wrap;
      }
      .parameter {
          margin-bottom: 10px;
      }
      .parameter textarea {
          width: 100%;
          box-sizing: border-box;
      }
      .table-container {
          width: 100%;
          overflow-x: auto;
          white-space: nowrap;
          margin-bottom: 2px;
      }
      table {
          border-collapse: collapse;
          width: 100%;
          margin-bottom: 2px;
          border: 3px solid #000;
          display: inline-block; /* Keeps tables in a single row */
      }
      th, td {
          border: 1px solid #ddd;
          text-align: left;
          width: auto;
      }
      #editableTable th:nth-child(1), #editableTable td:nth-child(1),
      #additionalTable th:nth-child(1), #additionalTable td:nth-child(1) {
          width: 100px; /* adjust as needed */
      }
      #editableTable th:nth-child(2), #editableTable td:nth-child(2),
      #additionalTable th:nth-child(2), #additionalTable td:nth-child(2) {
          width: 200px; /* adjust as needed */
      }
      td.editing {
          padding: 0;
      }
      td input {
          width: 100%;
          box-sizing: border-box;
          padding: 8px;
          border: none;
          background-color: #fff;
      }
      /* Styles specific to bannerTable */
      .bannerTable {
          width: 100%;
          border-collapse: collapse;
          text-align: center;
          margin-bottom: 20px;
      }
      .bannerTable td {
          /* border: 1px solid #ddd; */ 
          padding: 16px;
          font-size: 24px;
      }
      .bannerTable .number {
          font-size: 20px;
          font-weight: bold;
      }
      .bannerTable .unit {
          font-size: 12px;
          color: #555;
      }
      /* Update button styles */
      #updateButton {
          color: black;
          padding: 10px;
          border: none;
          cursor: pointer;
      }
      @keyframes colorCycle {
          0% { background-color: #007bff; }
          25% { background-color: #6610f2; }
          50% { background-color: #6f42c1; }
          75% { background-color: #e83e8c; }
          100% { background-color: #dc3545; }
      }

      #updateButton.loading {
          animation: colorCycle 2s infinite;
      }
    </style>
  </head>
  <body>
    <h1>MESC Web Cal</h1>
    <div class="tab-container">
      <div class="tab-buttons">
        <button onclick="openTab('tab1')">Settings</button>
        <button onclick="openTab('tab2')">Messages</button>
      </div>
      <div id="tab1" class="tab-content">
        <div id="container1">
          <table class="bannerTable">
            <tr>
              <td>
                <div class="number" id="error_value">-</div>
                <div class="unit">Error</div>
              </td>
              <td>
                <div class="number" id="vbus_value">-</div>
                <div class="unit">vbus</div>
              </td>
              <td>
                <div class="number" id="ehz_value">-</div>
                <div class="unit">eHz</div>
              </td>
              <td>
                <div class="number" id="TMOT_value">-</div>
                <div class="unit">TMOT</div>
              </td>
              <td>
                <div class="number" id="TMOS_value">-</div>
                <div class="unit">TMOS</div>
              </td>
            </tr>
          </table>
          <div style="display: flex; align-items: center;">
            <button id="updateButton" onclick="updateButtonPress()">UPDATE</button>
          </div>
          <br>
          <br>
          <div class="table-container">
            <!-- First table -->
            <table id="editableTable">
              <tr>
                <td>pole_pairs</td>
                <td id="pole_pairs_value" class="editable">NaN</td>
              </tr>
              <tr>
                <td>curr_max</td>
                <td id="curr_max_value" class="editable">NaN</td>
              </tr>
              <tr>
                <td>p_max</td>
                <td id="p_max_value" class="editable">NaN</td>
              </tr>
              <tr>
                <td>fw_curr</td>
                <td id="fw_curr_value" class="editable">NaN</td>
              </tr>
              <tr>
                <td>SL_sensor</td>
                <td id="SL_sensor_value" class="editable">NaN</td>
              </tr>
              <tr>
                <td>motor_sensor</td>
                <td id="motor_sensor_value" class="editable">NaN</td>
              </tr>
              <tr>
                <td>input_opt</td>
                <td id="input_opt_value" class="editable">NaN</td>
              </tr>
              <tr>
                <td>ol_step</td>
                <td id="ol_step_value" class="editable">NaN</td>
              </tr>
              <tr>
                <td>uart_req</td>
                <td id="uart_req_value" class="editable">NaN</td>
              </tr>
            </table>
            <!-- Additional table -->
            <table id="additionalTable">
              <tr>
                <td>adc1_max</td>
                <td id="adc1_max_value" class="editable">NaN</td>
              </tr>
              <tr>
                <td>adc1_min</td>
                <td id="adc1_min_value" class="editable">NaN</td>
              </tr>
              <tr>
                <td>adc2_max</td>
                <td id="adc2_max_value" class="editable">NaN</td>
              </tr>
              <tr>
                <td>adc2_min</td>
                <td id="adc2_min_value" class="editable">NaN</td>
              </tr>
              <tr>
                <td>flux</td>
                <td id="flux_value" class="editable">NaN</td>
              </tr>
              <tr>
                <td>r_phase</td>
                <td id="r_phase_value" class="editable">NaN</td>
              </tr>
              <tr>
                <td>ld_phase</td>
                <td id="ld_phase_value" class="editable">NaN</td>
              </tr>
              <tr>
                <td>lq_phase</td>
                <td id="lq_phase_value" class="editable">NaN</td>
              </tr>
              <tr>
                <td>motor_pp</td>
                <td id="motor_pp_value" class="editable">NaN</td>
              </tr>
            </table>
            <!-- Additional table -->
            <table id="additionalTable">
              <tr>
                <td>error_all</td>
                <td id="error_all_value" class="editable">NaN</td>
              </tr>
              <tr>
                <td>curr_min</td>
                <td id="curr_min_value" class="editable">NaN</td>
              </tr>
              <tr>
                <td>p_min</td>
                <td id="p_min_value" class="editable">NaN</td>
              </tr>
              <tr>
                <td>pwm_freq</td>
                <td id="pwm_freq_value" class="editable">NaN</td>
              </tr>
	      <tr>
		<td>fw_ehz</td>
		<td id="fw_ehz_value" class="editable">NaN</td>
	      </tr>
	      <tr>
		<td>adc1</td>
		<td id="adc1_value" class="editable">NaN</td>
	      </tr>
	      <tr>
		<td>Vd</td>
		<td id="Vd_value" class="editable">NaN</td>
	      </tr>
	      <tr>
		<td>Vq</td>
		<td id="Vq_value" class="editable">NaN</td>
	      </tr>
            </table>
          </div>
	  <br>
	  <button onclick="sendCommand()">Send</button>
	  <input type="text" id="command_input" placeholder="MESC command">

        </div>
      </div>
      <div id="tab2" class="tab-content">
        <div id="container2">
          <div id="messages"></div>
        </div>
      </div>
    </div>
    <script>
      function openTab(tabId) {
          const tabs = document.querySelectorAll('.tab-content');
          tabs.forEach(tab => {
              tab.classList.remove('active');
          });
          document.getElementById(tabId).classList.add('active');
      }
      document.addEventListener('DOMContentLoaded', () => {
          openTab('tab1'); // Open the first tab by default
      });
      var gateway = `ws://${window.location.hostname}/ws`;
      var websocket;
      window.addEventListener('load', onLoad);

      function initWebSocket() {
          console.log('Trying to open a WebSocket connection...');
          websocket = new WebSocket(gateway);
          websocket.onopen = onOpen;
          websocket.onclose = onClose;
          websocket.onerror = onError;
          websocket.onmessage = onMessage;
      }

      function onOpen(event) {
          console.log('Log message: Connection opened');
      }

      function onClose(event) {
          console.log('Connection closed', event);
          setTimeout(function() {
              location.reload();
          }, 2000);
      }

      function onError(event) {
          console.error('WebSocket error:', event);
      }

      function onMessage(event) {
          console.log('Message received:', event.data);
          var messagesDiv = document.getElementById('messages');
          var message = document.createElement('div');
          message.className = 'message';
          message.textContent = event.data;
          messagesDiv.appendChild(message);
          messagesDiv.scrollTop = messagesDiv.scrollHeight;
          try {
              var json = JSON.parse(event.data);
              updateTable(json);
          } catch (e) {
              console.error('Error parsing JSON:', e);
          }
          // Hide spinner after table update
          hideLoadingSpinner();  
      }

      function truncateNumber(value, decimalPlaces) {
          if (isNaN(value)) return value; // Return as is if it's not a number
          return parseFloat(parseFloat(value).toFixed(decimalPlaces));
      }

      async function updateTable(data) {
          const entries = Object.entries(data);
          const totalEntries = entries.length;
          let count = 0;

          for (const [key, value] of entries) {
              let truncatedValue = value;
              switch (key) {
              case "ld_phase":
                  // truncatedValue = truncateNumber(value, 6);
                  break;
              case "lq_phase":
                  // truncatedValue = truncateNumber(value, 6);
                  break;
              case "flux":
                  // truncatedValue = truncateNumber(value, 6);
                  break;
              case "r_phase":
                  // truncatedValue = truncateNumber(value, 6);
                  break;
              case "Vq":
                  break;
              default:
                  truncatedValue = truncateNumber(value, 1);
                  break;
              }

              // Update editable table cells
              var valueElement = document.getElementById(key + "_value");
              if (valueElement) {
                  valueElement.textContent = truncatedValue;
              }

              // Update non-editable elements
              var nonEditableElement = document.getElementById(key);
              if (nonEditableElement) {
                  nonEditableElement.textContent = truncatedValue;
              }

              count++;
              // Test for last element and hide the spinner
              if (count === totalEntries) {
                  hideLoadingSpinner();
              }
          }
      }

      function onLoad(event) {
          initWebSocket();
          document.getElementById('command_input').addEventListener('keydown', function(event) {
              if (event.key === 'Enter') {
                  sendCommand();
              }
          });
          const tables = document.querySelectorAll('table');
          tables.forEach(table => {
              table.addEventListener('click', function(event) {
                  const target = event.target;
                  if (target.classList.contains('editable')) {
                      editCell(target);
                  }
              });
          });

          // Ensure the button has the correct ID and event listener
          const updateButton = document.getElementById('updateButton');
          updateButton.addEventListener('click', updateButtonPress);
      }

      function sendCommand() {
          var inputBox = document.getElementById('command_input');
          var command = inputBox.value;
          if (command) {
              websocket.send(command);
              console.log('Sent command:', command);
              // Clear the input box and reset the placeholder
              inputBox.value = '';
              inputBox.placeholder = 'MESC command';
          } else {
              console.warn('No command entered');
          }
      }

      function editCell(cell) {
          const currentValue = cell.textContent;
          cell.classList.add('editing');
          cell.innerHTML = `<input type="text" value="${currentValue}">`;
          const input = cell.querySelector('input');
          input.focus();
          input.addEventListener('blur', function() {
              saveCell(cell, input.value);
          });
          input.addEventListener('keydown', function(event) {
              if (event.key === 'Enter') {
                  saveCell(cell, input.value);
              }
          });
      }

      function saveCell(cell, newValue) {
          cell.classList.remove('editing');
          cell.textContent = newValue;
          const cellID = cell.id.slice(0, -6);
          const command = "set " + cellID + " " + newValue;
          websocket.send(command);
          onCellEdit(cell, newValue);
      }

      function onCellEdit(cell, newValue) {
          console.log('Cell edited:', cell, 'New value:', newValue);
          // Perform additional actions, e.g., sending data to the server
      }

      async function updateButtonPress() {
          console.log('Update button pressed');
          showLoadingSpinner(); // Show loading state
          try {
              const response = await fetch('/button');
              const data = await response.text();
              console.log('Response from server:', data);
          } catch (error) {
              console.error('Error:', error);
          } finally {
              // hideLoadingSpinner(); // Hide loading state
          }
      }

      function showLoadingSpinner() {
          const updateButton = document.getElementById('updateButton');
          updateButton.classList.add('loading'); // Add class to change button color
      }

      function hideLoadingSpinner() {
          const updateButton = document.getElementById('updateButton');
          updateButton.classList.remove('loading'); // Remove class to reset button color
      }
      </script>

  </body>
</html>

    )rawliteral";

    #endif
    