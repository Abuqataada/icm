function openNav() {
    document.getElementById("mySidebar").style.width = "250px";
    document.getElementById("main").style.marginLeft = "250px";
    document.querySelector(".openbtn").style.display = "none"; // Hide the button
  }
  
function closeNav() {
    document.getElementById("mySidebar").style.width = "0";
    document.getElementById("main").style.marginLeft= "0";
    document.querySelector(".openbtn").style.display = "inline-block"; // Show the button
  }










  /* const socket = io();

  socket.on('update_client_count', (count) => {
      connectedClientsCount = count;
      document.getElementById('clientCount').textContent = `Participants: ${connectedClientsCount}`;
  });
  
  socket.on('message', (message) => {
      const messagesDiv = document.getElementById('messages');
      const messageElement = document.createElement('p');
      messageElement.textContent = message;
      messagesDiv.appendChild(messageElement);
  });
  
  socket.on('display_results', (results) => {
      const resultsDiv = document.getElementById('results');
      resultsDiv.innerHTML = ''; // Clear existing results
  
      results.forEach(result => {
  const resultElement = document.createElement('p');
  resultElement.textContent = `User ID: ${result.user_id}, Name: ${result.user_name}, Question: ${result.question_index}, Answer: ${result.answer}, Result: ${result.result}, Response Time: ${result.response_time} ms`;
  resultsDiv.appendChild(resultElement);
      });
  });
  
  socket.on('new_question', (question) => {
      const messagesDiv = document.getElementById('messages');
      const questionElement = document.createElement('p');
      questionElement.textContent = `Question: ${question.question}`;
      messagesDiv.appendChild(questionElement);
  
      // Clear the answers section for the new question
      const answersDiv = document.getElementById('answers');
      answersDiv.innerHTML = '';
  });
  */