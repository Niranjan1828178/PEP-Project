document.addEventListener('DOMContentLoaded', () => {
    const coursesContainer = document.getElementById('courses-container');
    const subtopicsContainer = document.getElementById('subtopics-container');
    const subtopicsList = document.getElementById('subtopics-list');
    const subtopicContent = document.getElementById('subtopic-content');
    const errorMessage = document.getElementById('error-message');

    fetch('static/question.json')
        .then(response => response.json())
        .then(data => {
            const courses = Object.keys(data);
            courses.forEach(course => {
                const courseElement = document.createElement('button');
                courseElement.classList.add('px-6', 'py-3', 'bg-indigo-100', 'text-indigo-600', 'rounded-lg', 'font-semibold', 'hover:bg-indigo-200', 'transition-colors');
                courseElement.textContent = course;
                courseElement.addEventListener('click', () => loadSubtopics(course, data[course]));
                coursesContainer.appendChild(courseElement);
            });
        })
        .catch(error => console.error('Error loading courses:', error));

    function loadSubtopics(course, subtopics) {
        subtopicsContainer.classList.remove('hidden');
        subtopicsList.innerHTML = '';
        subtopicContent.src = '';
        errorMessage.classList.add('hidden');
        subtopics.forEach(subtopic => {
            const subtopicElement = document.createElement('div');
            subtopicElement.classList.add('p-4', 'bg-gray-50', 'rounded-lg', 'shadow-md', 'cursor-pointer');
            subtopicElement.innerHTML = `
                <h4 class="text-lg font-semibold text-gray-800">${subtopic.subtopic}</h4>
            `;
            subtopicElement.addEventListener('click', () => {
                window.open(subtopic.link, '_blank');
            });
            subtopicsList.appendChild(subtopicElement);
        });
    }
});
