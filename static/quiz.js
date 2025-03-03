let selectedSubject = '';
    // Function to select the subject and render questions
function selectSubject(subject) {
    selectedSubject = subject;
    localStorage.setItem('subject', selectedSubject);

document.getElementById('subject').setAttribute('value', `${selectedSubject}`);
let btns=document.querySelector('.btn-group');
btns.innerHTML = `${selectedSubject}`;
btns.classList.add('textbtn');

    renderQuestions();
}


async function renderSubjects() {
    const subjectsContainer = document.querySelector('.btn-group');
    subjectsContainer.innerHTML = '';  // Clear any existing subjects
    var question=await fetch("static/question.json");
    var data= await question.json();
    var subjects=Object.keys(data);
    let k=1;
    subjects.forEach(subject => {
        const subjectElement = document.createElement('button');
        if(k==1)
             subjectElement.classList.add('btn', 'btn-primary', 'subject-btn');
        else if(k==subject.length)
             subjectElement.classList.add('btn', 'btn-success', 'subject-btn');
        else
            subjectElement.classList.add('btn', 'btn-secondary', 'subject-btn');
        subjectElement.textContent = subject;
        subjectElement.addEventListener('click', () => selectSubject(subject));
        subjectsContainer.appendChild(subjectElement);
    });

}

renderSubjects()
    // Function to render questions based on the selected subject
async function renderQuestions() {
    if (!selectedSubject) {
        return;
    }

    const questionsContainer = document.getElementById('questions-container');
    const submitBtn = document.getElementById('submitBtn');
    questionsContainer.innerHTML = '';  // Clear any existing questions
    var question=await fetch("static/question.json");
    var data= await question.json();
    var que=data[selectedSubject];
    let n=[];
    let quiz=[];
    for(var i=0;i<10;i++){
        let rn = Math.floor(Math.random() * 20);
        console.log(`out:${rn}`);
        while(n.includes(rn)){
            rn = Math.floor(Math.random() * 20);;
            console.log(`in:${rn}`);
        }
        n.push(rn);
        quiz.push(que[rn]);

    }
    let k=1
    // Render questions and options
    quiz.forEach(question => {
        const questionElement = document.createElement('div');
        questionElement.classList.add('question-container', 'form-group');
        let optionsHTML = '';
       
        question.options.forEach(option => {
            optionsHTML += `
                <div class="form-check">
                    <input class="form-check-input" type="radio" name="${question.id}" value="${option}" required>
                    <label class="form-check-label">${option}</label>
                </div>
            `;
        });
        questionElement.innerHTML = `
            <label for="${question.id}">${k}. ${question.question}</label>
            ${optionsHTML}
        `;
        k+=1;   
        questionsContainer.appendChild(questionElement);
    });

    // Show the Submit button once questions are rendered
    submitBtn.style.display = 'block';
}

