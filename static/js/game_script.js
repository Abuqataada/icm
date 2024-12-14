let timerInterval;
let timeLeft = 0; // Time left in seconds
let currentQuestionIndex = null;
const socket = io();
let connectedClientsCount = 0;

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

let questionStartTime = null;

socket.on('new_question', (question) => {
  currentQuestionIndex = question.index;
  
  const questionDiv = document.getElementById('question');
  questionDiv.textContent = question.question;
  
  const choicesDiv = document.getElementById('choices');
  choicesDiv.innerHTML = '';
  
  // Check if the question is not empty before starting the timer
  if (question.question !== '' && question.choices.some(choice => choice !== '')) {
      // Reset and start timer for a specific duration (e.g., 30 seconds)
      startTimer(15); // Set duration as needed
      questionStartTime = Date.now();
  } else {
      clearInterval(timerInterval); // Stop the timer if question is empty
      document.getElementById('timer').textContent = '00:00'; // Reset timer display
  }
  
  // Create buttons for each choice
  question.choices.forEach((choice, index) => {
      const choiceButton = document.createElement('button');
      choiceButton.textContent = choice;
      choiceButton.onclick = () => submitAnswer(index + 1); // Note index + 1 to match the server's expected answer index
      choicesDiv.appendChild(choiceButton);
  });
  
  // Enable all choice buttons
  const buttons = choicesDiv.getElementsByTagName('button');
  for (let button of buttons) {
      button.disabled = false; // Enable the button
  }
      });
      
      

function submitAnswer(choice) {
    const responseTime = (Date.now() - questionStartTime) / 1000; // Convert to seconds
    console.log(responseTime)
    const formattedResponseTime = responseTime.toFixed(1); // Format to one decimal place

    // Disable all choice buttons
    const choicesDiv = document.getElementById('choices');
    const buttons = choicesDiv.getElementsByTagName('button');
    for (let button of buttons) {
button.disabled = true; // Disable the button
    }

    socket.emit('submit_answer', {
question_index: currentQuestionIndex,
answer: choice,
response_time: parseFloat(formattedResponseTime) // Send as a float
    });
}

function startTimer(duration) {
    timeLeft = duration;
    clearInterval(timerInterval); // Clear any existing timers

    timerInterval = setInterval(() => {
if (timeLeft <= 0) {
    clearInterval(timerInterval);
    // Handle time up (e.g., submit answer automatically or notify user)
    submitAnswer(0);
    // Disable all choice buttons
    const choicesDiv = document.getElementById('choices');
    const buttons = choicesDiv.getElementsByTagName('button');
    for (let button of buttons) {
button.disabled = true; // Disable the button
    }
    // Emit event to notify the server that time is up
    //socket.emit('time_up');
} else {
    timeLeft--;
    updateTimerDisplay();
}
    }, 1000);
}

function updateTimerDisplay() {
    const minutes = String(Math.floor(timeLeft / 60)).padStart(2, '0');
    const seconds = String(timeLeft % 60).padStart(2, '0');
    document.getElementById('timer').textContent = `${minutes}:${seconds}`;
}