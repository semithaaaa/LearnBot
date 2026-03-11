// Wait for Step 2 for actual API wiring.
// Step 1: UI Interactivity ONLY (Tabs, Drag & Drop, Modals)

document.addEventListener('DOMContentLoaded', () => {

    // --- 1. Tab Switching (PDF vs Text) ---
    const inputTabs = document.querySelectorAll('.tab-btn[data-target]');
    const inputModes = document.querySelectorAll('.input-mode');

    inputTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Reset tabs
            inputTabs.forEach(t => {
                t.classList.remove('bg-white', 'shadow-sm', 'text-slate-800');
                t.classList.add('text-slate-500', 'hover:text-slate-700');
            });
            // Activate clicked
            tab.classList.remove('text-slate-500', 'hover:text-slate-700');
            tab.classList.add('bg-white', 'shadow-sm', 'text-slate-800');

            // Switch content
            inputModes.forEach(mode => mode.classList.add('hidden'));
            document.getElementById(tab.dataset.target).classList.remove('hidden');
        });
    });

    // --- 2. Quiz Tabs ---
    const quizTabs = document.querySelectorAll('.quiz-tab');
    const quizContainers = document.querySelectorAll('.quiz-container');

    quizTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            quizTabs.forEach(t => {
                t.classList.remove('active', 'text-primary-600', 'border-b-2', 'border-primary-500');
                t.classList.add('text-slate-500', 'hover:text-slate-700');
            });
            tab.classList.remove('text-slate-500', 'hover:text-slate-700');
            tab.classList.add('active', 'text-primary-600', 'border-b-2', 'border-primary-500');

            quizContainers.forEach(c => c.classList.add('hidden'));
            document.getElementById(tab.dataset.target).classList.remove('hidden');
        });
    });

    // --- 3. Drag and Drop PDF Upload ---
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-upload');
    const fileInfo = document.getElementById('file-info');
    const fileName = document.getElementById('file-name');
    const removeFileBtn = document.getElementById('remove-file');

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) { e.preventDefault(); e.stopPropagation(); }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.add('dragover'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.remove('dragover'), false);
    });

    dropZone.addEventListener('drop', handleDrop, false);
    fileInput.addEventListener('change', (e) => handleFiles(e.target.files));

    function handleDrop(e) {
        let dt = e.dataTransfer;
        let files = dt.files;
        handleFiles(files);
    }

    function handleFiles(files) {
        if (files.length > 0 && files[0].type === "application/pdf") {
            fileName.textContent = files[0].name;
            dropZone.classList.add('hidden');
            fileInfo.classList.remove('hidden');
        } else {
            alert('Please upload a valid PDF file.');
        }
    }

    removeFileBtn.addEventListener('click', () => {
        fileInput.value = ''; // clear input
        fileInfo.classList.add('hidden');
        dropZone.classList.remove('hidden');
    });

    // --- 3.5 Drag and Drop Image Upload ---
    const imageDropZone = document.getElementById('image-drop-zone');
    const imageFileInput = document.getElementById('image-upload');
    const imageFileInfo = document.getElementById('image-file-info');
    const imageFileName = document.getElementById('image-file-name');
    const removeImageFileBtn = document.getElementById('remove-image-file');

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        if (imageDropZone) imageDropZone.addEventListener(eventName, preventDefaults, false);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        if (imageDropZone) imageDropZone.addEventListener(eventName, () => imageDropZone.classList.add('dragover'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        if (imageDropZone) imageDropZone.addEventListener(eventName, () => imageDropZone.classList.remove('dragover'), false);
    });

    if (imageDropZone) imageDropZone.addEventListener('drop', handleImageDrop, false);
    if (imageFileInput) imageFileInput.addEventListener('change', (e) => handleImageFiles(e.target.files));

    function handleImageDrop(e) {
        let dt = e.dataTransfer;
        let files = dt.files;
        handleImageFiles(files);
    }

    function handleImageFiles(files) {
        if (files.length > 0 && files[0].type.startsWith("image/")) {
            imageFileName.textContent = files[0].name;
            imageDropZone.classList.add('hidden');
            imageFileInfo.classList.remove('hidden');
            // Assign to input
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(files[0]);
            imageFileInput.files = dataTransfer.files;
        } else {
            alert('Please upload a valid image file (JPG, PNG).');
        }
    }

    if (removeImageFileBtn) removeImageFileBtn.addEventListener('click', () => {
        imageFileInput.value = '';
        imageFileInfo.classList.add('hidden');
        imageDropZone.classList.remove('hidden');
    });

    // --- 4. Voice Widget Toggle & Logic ---
    const voiceFab = document.getElementById('voice-fab');
    const voiceChatBubble = document.getElementById('voice-chat-bubble');
    const closeChatBtn = document.getElementById('close-chat');
    const aiStatusPulse = document.getElementById('ai-status-pulse');
    const aiStatusPulseRing = aiStatusPulse.querySelector('.animate-ping');
    const aiMessageContainer = document.querySelector('#voice-chat-bubble p.text-sm');
    const aiSubMessageContainer = document.querySelector('#voice-chat-bubble p.text-xs');

    let isListening = false;
    let recognition;

    if ('webkitSpeechRecognition' in window) {
        recognition = new webkitSpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';

        recognition.onstart = function () {
            isListening = true;
            aiStatusPulse.classList.add('bg-red-100');
            aiStatusPulseRing.classList.add('bg-red-400');
            aiStatusPulse.querySelector('svg').classList.replace('text-primary-600', 'text-red-600');
            aiMessageContainer.textContent = "Listening...";
            aiSubMessageContainer.textContent = "Speak your question now.";
        };

        recognition.onresult = async function (event) {
            const transcript = event.results[0][0].transcript;

            aiStatusPulse.classList.remove('bg-red-100');
            aiStatusPulseRing.classList.remove('bg-red-400');
            aiStatusPulse.querySelector('svg').classList.replace('text-red-600', 'text-primary-600');

            aiMessageContainer.textContent = "Processing...";
            aiSubMessageContainer.textContent = `You said: "${transcript}"`;

            try {
                const res = await fetch(`${API_URL}/api/voice-chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: transcript,
                        context: currentExtractedText
                    })
                });

                if (!res.ok) {
                    let errStr = "Voice API failed";
                    try {
                        const errData = await res.json();
                        errStr = errData.detail || JSON.stringify(errData);
                    } catch (e) {
                        errStr = "HTTP " + res.status;
                    }
                    throw new Error(`${errStr}`);
                }
                const data = await res.json();

                aiMessageContainer.textContent = "Agent says:";
                // Truncate response for UI
                let shortRes = data.response;
                if (shortRes.length > 80) shortRes = shortRes.substring(0, 80) + '...';
                aiSubMessageContainer.textContent = shortRes;

                speakResponse(data.response);

            } catch (error) {
                aiMessageContainer.textContent = "Error occurred.";
                aiSubMessageContainer.textContent = error.message;
            }
        };

        recognition.onerror = function (event) {
            aiMessageContainer.textContent = "Could not hear you.";
            aiSubMessageContainer.textContent = "Click mic to try again.";
            resetMicUI();
        };

        recognition.onend = function () {
            isListening = false;
            resetMicUI();
        };
    } else {
        aiMessageContainer.textContent = "Speech not supported";
        aiSubMessageContainer.textContent = "Please use Chrome.";
    }

    function resetMicUI() {
        if (!isListening) {
            aiStatusPulse.classList.remove('bg-red-100');
            aiStatusPulseRing.classList.remove('bg-red-400');
            aiStatusPulse.querySelector('svg').className = "w-8 h-8 text-primary-600";
        }
    }

    function speakResponse(text) {
        if ('speechSynthesis' in window) {
            // Strip markdown asterisks for cleaner speech
            const cleanText = text.replace(/[*#]/g, '');
            const utterance = new SpeechSynthesisUtterance(cleanText);
            utterance.rate = 1.0;
            utterance.pitch = 1.0;

            utterance.onstart = () => {
                aiStatusPulse.classList.add('bg-blue-100');
                aiStatusPulseRing.classList.add('bg-blue-400');
                aiStatusPulse.querySelector('svg').classList.replace('text-primary-600', 'text-blue-600');
            };

            utterance.onend = () => {
                aiStatusPulse.classList.remove('bg-blue-100');
                aiStatusPulseRing.classList.remove('bg-blue-400');
                aiStatusPulse.querySelector('svg').classList.replace('text-blue-600', 'text-primary-600');
                aiMessageContainer.textContent = "I'm ready to listen.";
                aiSubMessageContainer.textContent = "Click icon to ask another question.";
            };

            window.speechSynthesis.speak(utterance);
        }
    }

    voiceFab.addEventListener('click', () => {
        voiceChatBubble.classList.toggle('hidden');
    });

    closeChatBtn.addEventListener('click', () => {
        voiceChatBubble.classList.add('hidden');
        if (isListening) { recognition.stop(); }
        if (window.speechSynthesis.speaking) { window.speechSynthesis.cancel(); }
    });

    aiStatusPulse.addEventListener('click', () => {
        if (isListening) {
            recognition.stop();
        } else {
            if (window.speechSynthesis.speaking) window.speechSynthesis.cancel();
            recognition.start();
        }
    });

    // --- 5. UI Controls (Counters) ---
    document.querySelectorAll('.count-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const targetId = e.currentTarget.dataset.target;
            const action = e.currentTarget.dataset.action;
            const inputEl = document.getElementById(targetId);
            let val = parseInt(inputEl.value);

            if (action === 'inc' && val < 50) {
                inputEl.value = val + 1;
            } else if (action === 'dec' && val > 1) {
                inputEl.value = val - 1;
            }
        });
    });

    // --- 6. API Integration ---
    const defaultApiUrl = 'http://127.0.0.1:8000';
    const metaApi = document.querySelector('meta[name="api-url"]');
    const API_URL = (metaApi && metaApi.content && metaApi.content !== '%API_URL%') ? metaApi.content : defaultApiUrl;
    let currentExtractedText = ""; // Store for Voice Agent context later

    const btnExtractText = document.getElementById('btn-extract-text');
    if (btnExtractText) {
        btnExtractText.addEventListener('click', async () => {
            const imageInput = document.getElementById('image-upload');
            if (!imageInput.files || imageInput.files.length === 0) {
                alert("Please select an image file first.");
                return;
            }

            const spinner = document.getElementById('extract-spinner');
            btnExtractText.disabled = true;
            spinner.classList.remove('hidden');

            try {
                const formData = new FormData();
                formData.append('file', imageInput.files[0]);

                // Append selected OCR model
                const ocrModel = document.getElementById('ocr-model-select').value;
                formData.append('ocr_model', ocrModel);

                const res = await fetch(`${API_URL}/extract-image`, { method: 'POST', body: formData });
                if (!res.ok) {
                    let errStr = "Image OCR Error";
                    try {
                        const errData = await res.json();
                        errStr = errData.detail || JSON.stringify(errData);
                    } catch (e) {
                        errStr = "HTTP " + res.status;
                    }
                    throw new Error(`${errStr}`);
                }
                const data = await res.json();

                // Put text into Raw Text area and switch to it
                document.getElementById('raw-text').value = data.text;
                document.querySelector('.tab-btn[data-target="text-input-mode"]').click();

            } catch (error) {
                alert("Error: " + error.message);
            } finally {
                btnExtractText.disabled = false;
                spinner.classList.add('hidden');
            }
        });
    }

    document.getElementById('btn-summarize').addEventListener('click', async () => {
        const textMode = !document.getElementById('text-input-mode').classList.contains('hidden');
        const textVal = document.getElementById('raw-text').value;
        const fileInput = document.getElementById('file-upload');

        if (textMode && !textVal.trim()) {
            alert("Please enter some text.");
            return;
        }
        if (!textMode && (!fileInput.files || fileInput.files.length === 0)) {
            alert("Please select a PDF file.");
            return;
        }

        // Show Loader
        document.getElementById('summary-empty').classList.add('hidden');
        document.getElementById('summary-content').classList.add('hidden');
        document.getElementById('summary-loader').classList.remove('hidden');
        document.getElementById('compression-badge').classList.add('hidden');

        try {
            const formData = new FormData();
            if (textMode) formData.append('text', textVal);
            else formData.append('file', fileInput.files[0]);

            const res = await fetch(`${API_URL}/summarize`, { method: 'POST', body: formData });
            if (!res.ok) {
                let errStr = "Summarization API Error";
                try {
                    const errData = await res.json();
                    errStr = errData.detail || JSON.stringify(errData);
                } catch (e) {
                    errStr = "HTTP " + res.status;
                }
                throw new Error(`${errStr}`);
            }
            const data = await res.json();

            document.getElementById('summary-loader').classList.add('hidden');
            document.getElementById('summary-content').innerHTML = data.summary.replace(/\n\n/g, '<br><br>');
            document.getElementById('summary-content').classList.remove('hidden');

            // Compression Math
            const comp = Math.round((1 - (data.summary_length / data.original_length)) * 100);
            document.getElementById('compression-badge').textContent = `${comp}% COMPRESSED`;
            document.getElementById('compression-badge').classList.remove('hidden');

            // Store summary context for Gemini later
            currentExtractedText = data.summary;

        } catch (error) {
            alert("Error: " + error.message);
            document.getElementById('summary-loader').classList.add('hidden');
            document.getElementById('summary-empty').classList.remove('hidden');
        }
    });

    document.getElementById('btn-quiz').addEventListener('click', async () => {
        const textMode = !document.getElementById('text-input-mode').classList.contains('hidden');
        const textVal = document.getElementById('raw-text').value;
        const fileInput = document.getElementById('file-upload');

        if (textMode && !textVal.trim()) { alert("Please enter some text."); return; }
        if (!textMode && (!fileInput.files || fileInput.files.length === 0)) { alert("Please select a file."); return; }

        document.getElementById('quiz-empty').classList.add('hidden');
        quizContainers.forEach(c => c.classList.add('hidden'));
        document.getElementById('quiz-loader').classList.remove('hidden');

        try {
            const formData = new FormData();
            if (textMode) formData.append('text', textVal);
            else formData.append('file', fileInput.files[0]);

            // Append custom counts
            formData.append('num_mcq', document.getElementById('mcq-count').value);
            formData.append('num_tf', document.getElementById('tf-count').value);
            formData.append('num_fib', document.getElementById('fib-count').value);
            formData.append('num_flash', document.getElementById('flash-count').value);

            const res = await fetch(`${API_URL}/generate-quizzes`, { method: 'POST', body: formData });
            if (!res.ok) {
                let errStr = "Quiz API Error";
                try {
                    const errData = await res.json();
                    errStr = errData.detail || JSON.stringify(errData);
                } catch (e) {
                    errStr = "HTTP " + res.status;
                }
                throw new Error(`${errStr}`);
            }
            const data = await res.json();

            document.getElementById('quiz-loader').classList.add('hidden');
            renderQuizzes(data);

            // Show the currently active tab content
            const activeTabTarget = document.querySelector('.quiz-tab.active').dataset.target;
            document.getElementById(activeTabTarget).classList.remove('hidden');

        } catch (error) {
            alert("Error: " + error.message);
            document.getElementById('quiz-loader').classList.add('hidden');
            document.getElementById('quiz-empty').classList.remove('hidden');
        }
    });

    // --- Quiz Rendering Helpers ---
    function renderQuizzes(data) {
        // Render MCQs
        const mcqCont = document.getElementById('q-mcq');
        mcqCont.innerHTML = data.mcqs.map((q, i) => `
            <div class="p-4 border border-slate-200 rounded-xl hover:border-primary-300 transition-colors bg-slate-50 relative overflow-hidden group">
                <div class="absolute left-0 top-0 bottom-0 w-1 bg-primary-500"></div>
                <h3 class="font-semibold text-slate-800 mb-3 ml-2">${i + 1}. ${q.question}</h3>
                <div class="flex flex-col gap-2 ml-2">
                    ${q.options.map(o => `
                        <div class="px-4 py-2 border border-slate-200 rounded-lg hover:bg-primary-50 cursor-pointer transition-colors text-sm text-slate-600">
                            ${o}
                        </div>
                    `).join('')}
                </div>
                <div class="mt-4 ml-2 pt-3 border-t border-dashed border-slate-200 text-green-600 font-semibold text-sm">
                    Answer: ${q.answer}
                </div>
            </div>
        `).join('') || '<p class="text-slate-400">No MCQs generated.</p>';

        // Render TF
        const tfCont = document.getElementById('q-tf');
        tfCont.innerHTML = data.true_false.map((q, i) => `
            <div class="p-4 border border-slate-200 rounded-xl hover:border-secondary-300 transition-colors bg-slate-50 relative overflow-hidden">
                <div class="absolute left-0 top-0 bottom-0 w-1 bg-secondary-500"></div>
                <h3 class="font-semibold text-slate-800 mb-3 ml-2">${i + 1}. ${q.question}</h3>
                <div class="flex gap-4 ml-2">
                    <div class="flex-1 px-4 py-2 text-center border border-slate-200 bg-white rounded-lg hover:bg-secondary-50 cursor-pointer font-medium text-slate-700">True</div>
                    <div class="flex-1 px-4 py-2 text-center border border-slate-200 bg-white rounded-lg hover:bg-secondary-50 cursor-pointer font-medium text-slate-700">False</div>
                </div>
                <div class="mt-4 ml-2 pt-3 border-t border-dashed border-slate-200 text-green-600 font-semibold text-sm">Answer: ${q.answer}</div>
            </div>
        `).join('') || '<p class="text-slate-400">No True/False generated.</p>';

        // Render FIB
        const fibCont = document.getElementById('q-fib');
        fibCont.innerHTML = data.fill_in_the_blank.map((q, i) => `
            <div class="p-4 border border-slate-200 rounded-xl hover:border-blue-300 transition-colors bg-slate-50 relative overflow-hidden">
                 <div class="absolute left-0 top-0 bottom-0 w-1 bg-blue-500"></div>
                 <h3 class="font-semibold text-slate-800 mb-3 ml-2 leading-relaxed">${i + 1}. ${q.question}</h3>
                 <div class="mt-2 ml-2 pt-3 border-t border-dashed border-slate-200 text-green-600 font-semibold text-sm">Answer: ${q.answer}</div>
            </div>
        `).join('') || '<p class="text-slate-400">No Fill-in-the-blanks generated.</p>';

        // Render Flashcards
        const flashCont = document.getElementById('q-flash');
        flashCont.innerHTML = data.flashcards.map(f => `
            <div class="flashcard-wrapper group">
                <div class="flashcard-inner relative w-full h-full shadow-sm rounded-xl transition-all duration-500 transform-style-3d">
                    <div class="flashcard-front absolute w-full h-full backface-hidden flex items-center justify-center p-4 bg-primary-50 border border-primary-200 rounded-xl">
                        <span class="text-lg font-bold text-primary-700 text-center">${f.term}</span>
                    </div>
                    <div class="flashcard-back absolute w-full h-full backface-hidden flex items-center justify-center p-4 bg-slate-800 rounded-xl transform rotate-y-180 text-white shadow-lg overflow-y-auto">
                        <span class="text-sm font-medium text-center leading-relaxed text-slate-200 hover:text-white transition-colors cursor-default">${f.definition}</span>
                    </div>
                </div>
            </div>
        `).join('') || '<p class="text-slate-400 col-span-2 text-center">No Flashcards generated.</p>';

        // Add click listener to flip flashcards manually (in addition to hover)
        document.querySelectorAll('.flashcard-inner').forEach(card => {
            card.addEventListener('click', function () {
                this.classList.toggle('rotate-y-180');
            });
        });
    }

});
