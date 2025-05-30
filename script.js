document.addEventListener('DOMContentLoaded', () => {
    const guessInput = document.getElementById('guessInput');
    const submitGuessButton = document.getElementById('submitGuess');
    const messageElement = document.getElementById('message');
    const guessesCountElement = document.getElementById('guessesCount');

    let randomNumber = Math.floor(Math.random() * 100) + 1;
    let guesses = 0;

    submitGuessButton.addEventListener('click', () => {
        const userGuess = parseInt(guessInput.value);
        guesses++;
        guessesCountElement.textContent = guesses;

        if (isNaN(userGuess) || userGuess < 1 || userGuess > 100) {
            messageElement.textContent = 'Please enter a valid number between 1 and 100.';
            messageElement.style.color = 'red';
            return;
        }

        if (userGuess === randomNumber) {
            messageElement.textContent = `Congratulations! You guessed the number ${randomNumber} in ${guesses} guesses.`;
            messageElement.style.color = 'green';
            guessInput.disabled = true;
            submitGuessButton.disabled = true;
        } else if (userGuess < randomNumber) {
            messageElement.textContent = 'Too low! Try again.';
            messageElement.style.color = 'orange';
        } else {
            messageElement.textContent = 'Too high! Try again.';
            messageElement.style.color = 'orange';
        }
        guessInput.value = ''; // Clear the input field
        guessInput.focus(); // Focus on the input field for the next guess
    });
});
