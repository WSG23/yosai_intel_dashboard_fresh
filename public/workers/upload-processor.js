// Web Worker for processing file chunks
self.onmessage = function (e) {
    const { type, taskId, data } = e.data;

    switch (type) {
        case 'process_chunk':
            try {
                // Simulate chunk processing
                const processedData = processChunk(data);

                self.postMessage({
                    type: 'chunk_complete',
                    taskId: taskId,
                    data: processedData
                });
            } catch (error) {
                self.postMessage({
                    type: 'error',
                    taskId: taskId,
                    data: { error: error.message }
                });
            }
            break;

        case 'parse_csv':
            // CSV parsing logic
            const parsed = parseCSVData(data.content);
            self.postMessage({
                type: 'parse_complete',
                taskId: taskId,
                data: parsed
            });
            break;
    }
};

function processChunk(data) {
    // Implement chunk processing logic
    return {
        processed: true,
        rowCount: data.length
    };
}

function parseCSVData(content) {
    // Basic CSV parsing
    const lines = content.split('\n');
    const headers = lines[0].split(',');
    const rows = [];

    for (let i = 1; i < lines.length; i++) {
        if (lines[i].trim()) {
            const values = lines[i].split(',');
            const row = {};
            headers.forEach((header, index) => {
                row[header.trim()] = values[index]?.trim() || '';
            });
            rows.push(row);
        }
    }

    return { headers, rows };
}