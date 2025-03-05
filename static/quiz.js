function getQueryParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

let selectedSubject = '';

function selectSubject(subject) {
    selectedSubject = subject;
    localStorage.setItem('subject', selectedSubject);
    document.getElementById('subject').value = selectedSubject;
    
    // Update button styles for selected subject
    document.querySelectorAll('.subject-btn').forEach(btn => {
        btn.classList.remove('bg-indigo-600', 'text-white');
        btn.classList.add('bg-indigo-100', 'text-indigo-600');
        if (btn.textContent === subject) {
            btn.classList.remove('bg-indigo-100', 'text-indigo-600');
            btn.classList.add('bg-indigo-600', 'text-white');
        }
    });

    renderQuestions();
}

async function renderSubjects() {
    const subjectsContainer = document.querySelector('#subject-container');
    subjectsContainer.innerHTML = '';  // Clear existing subjects
    
    try {
        const response = await fetch("static/question.json");
        const data = await response.json();
        const subjects = Object.keys(data);
        const preselectedTopic = getQueryParam('topic');
        
        subjects.forEach(subject => {
            const subjectElement = document.createElement('button');
            subjectElement.classList.add(
                'px-6', 'py-3', 
                'bg-indigo-100', 
                'text-indigo-600', 
                'rounded-lg', 
                'font-semibold', 
                'hover:bg-indigo-200', 
                'transition-colors', 
                'subject-btn'
            );
            subjectElement.textContent = subject;
            subjectElement.addEventListener('click', () => selectSubject(subject));
            subjectsContainer.appendChild(subjectElement);
            
            // Auto-select the topic if it matches the URL parameter
            if (subject === preselectedTopic) {
                setTimeout(() => selectSubject(subject), 100);
            }
        });
    } catch (error) {
        console.error('Error loading subjects:', error);
    }
}

async function renderQuestions() {
    if (!selectedSubject) return;

    const questionsContainer = document.getElementById('questions-container');
    const submitBtn = document.getElementById('submitBtn');
    questionsContainer.innerHTML = '';

    try {
        const response = await fetch("static/question.json");
        const data = await response.json();
        const questions = data[selectedSubject];
        const selectedQuestions = getRandomQuestions(questions, 10);

        selectedQuestions.forEach((question, index) => {
            const questionElement = document.createElement('div');
            questionElement.classList.add('mb-8', 'p-6', 'bg-gray-50', 'rounded-lg');
            
            let optionsHTML = '<div class="space-y-3 mt-4">';
            question.options.forEach(option => {
                optionsHTML += `
                    <div class="flex items-center">
                        <input type="radio" 
                               id="${question.id}_${option}" 
                               name="${question.id}" 
                               value="${option}" 
                               required
                               class="w-4 h-4 text-indigo-600 border-gray-300 focus:ring-indigo-500">
                        <label for="${question.id}_${option}" 
                               class="ml-3 text-gray-700">
                            ${option}
                        </label>
                    </div>
                `;
            });
            optionsHTML += '</div>';

            questionElement.innerHTML = `
                <p class="text-lg font-medium text-gray-900">
                    ${index + 1}. ${question.question}
                </p>
                ${optionsHTML}
            `;
            
            questionsContainer.appendChild(questionElement);
        });

        submitBtn.disabled = false;
        submitBtn.classList.remove('opacity-50', 'cursor-not-allowed');
    } catch (error) {
        console.error('Error loading questions:', error);
    }
}

function getRandomQuestions(questions, count) {
    const shuffled = [...questions].sort(() => 0.5 - Math.random());
    return shuffled.slice(0, count);
}

// Initialize subjects when page loads
renderSubjects();