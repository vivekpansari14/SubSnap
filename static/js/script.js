document.getElementById('generate-btn').addEventListener('click', function() {
    const fileUpload = document.getElementById('file-upload').files[0];
    const colorPicker = document.getElementById('color-picker').value;
    const fontSize = document.getElementById('font-size').value;
    const maxWords = document.getElementById('max-words').value;
    const colorWords = document.getElementById('color-words').value;

    if (fileUpload) {
        const formData = new FormData();
        formData.append('file', fileUpload);  // Append the file
        formData.append('color', colorPicker);
        formData.append('font_size', fontSize);
        formData.append('max_words', maxWords);
        formData.append('color_words', colorWords);

        // Send data to Flask server via POST request
        fetch('/generate_subtitle', {
            method: 'POST',
            body: formData,
        })
        .then(data => {
            loader.style.display = "none";
            if (data.download_url) {
              const downloadLink = document.createElement('a');
              downloadLink.href = data.download_url;
              downloadLink.download = 'subtitles.srt';
              downloadLink.textContent = 'Download Subtitle File';
              downloadLink.className = 'download-link';
              resultDiv.innerHTML = '';
              resultDiv.appendChild(downloadLink);
            } else if (data.error) {
              resultDiv.innerHTML = '<p style="color:red;">' + data.error + '</p>';
            } else {
              resultDiv.innerHTML = '<p>Something went wrong.</p>';
            }
          })
          
        .then(response => response.json())
        .then(data => {
            const resultDiv = document.getElementById('result');
            if (data.subtitle) {
                resultDiv.textContent = `Generated Subtitle:\n${data.subtitle}`;
            } else {
                resultDiv.textContent = `Error: ${data.error}`;
            }
            resultDiv.style.display = 'block';
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while generating the subtitle.');
        });
    } else {
        alert("Please upload a file.");
    }
});
