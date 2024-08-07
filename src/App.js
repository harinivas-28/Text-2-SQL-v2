import React, { useState } from 'react';
import axios from 'axios';
import './App.css';
import sun from './sun.png'
import moon from './moon.png'
// import logo from './logo.png'

function App() {
    const [file, setFile] = useState(null);
    const [question, setQuestion] = useState('');
    const [result, setResult] = useState(null);
    const [query, setQuery] = useState('');
    const [error, setError] = useState(null);
    const [plots, setPlots] = useState([]);
    const [loading, setLoading] = useState(false);
    const [showDetails, setShowDetails] = useState(false);
    const [csvData, setCsvData] = useState({ columns: [], rows: [] });
    const [isDarkMode, setIsDarkMode] = useState(true); // Start in dark mode

    const toggleTheme = () => {
        setIsDarkMode(!isDarkMode);
        // You can add logic to apply CSS classes or toggle styles here
    };

    const handleFileChange = (event) => {
        const selectedFile = event.target.files[0];
        if (selectedFile && selectedFile.type === 'text/csv') {
            setFile(selectedFile);
            setError(null);
            setShowDetails(false); // Reset "Show Details" button state
        } else {
            setError({ message: 'Please upload a valid CSV file.' });
        }
    };

    const handleQuestionChange = (event) => {
        setQuestion(event.target.value);
    };

    const handleShowDetails = () => {
        if (file) {
            // Read and parse the CSV file
            const reader = new FileReader();
            reader.onload = (e) => {
                const text = e.target.result;
                const rows = text.split('\n').map(row => row.split(','));
                const columns = rows[0];
                const data = rows.slice(1, 30); 
                setCsvData({ columns, rows: data });
                setShowDetails(true);
            }; 
            reader.readAsText(file);
        }
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        if (!file) {
            setError({ message: 'Please upload a CSV file.' });
            return;
        }
        if (!question) {
            setError({ message: 'Please enter a question.' });
            return;
        }

        setLoading(true); 
        const formData = new FormData();
        formData.append('file', file);
        formData.append('question', question);

        const axiosSource = axios.CancelToken.source();
        const timeoutDuration = 120000; // Timeout duration in milliseconds (2 minutes)

        const timeoutPromise = new Promise((_, reject) =>
            setTimeout(() => {
                axiosSource.cancel(); // Cancel the request
                reject(new Error('Request timed out'));
            }, timeoutDuration)
        );

        try {
            const response = await Promise.race([
                axios.post('http://localhost:5000/api/query', formData, {
                    headers: {
                        'Content-Type': 'multipart/form-data',
                    },
                    cancelToken: axiosSource.token,
                }),
                timeoutPromise,
            ]);

            setQuery(response.data.query);
            setResult(response.data.result);
            setPlots(response.data.plots);
            setError(null);
        } catch (error) {
            if (axios.isCancel(error)) {
                setError({ message: 'Request canceled due to timeout.' });
            } else if (error.message === 'Request timed out') {
                setError({ message: 'Request timed out. Please try again.' });
            } else {
                console.error('Error submitting query:', error);
                setError(error.response ? error.response.data : { message: 'Error submitting query' });
            }
            setQuery('');
            setResult(null);
            setPlots([]);
        } finally {
            setLoading(false); // Hide loader when request completes
        }
    };

    return (
        <div className={`App ${isDarkMode ? 'dark-theme' : 'light-theme'}`}>
            {/* <nav className="navbar">
                <div className="logo-container">
                <img className='logo-img' src={logo} alt="Your Logo" />
                <span className="company-name">SQLify</span>
                </div>
                <button className="about-button">About</button>
            </nav> */}
            <div className='stars'></div>
            <div className='stars2'></div>
            <div className='stars3'></div>
            <div className="background-animation"></div> {/* Background animation */}
            {loading && (
                <div class="loader">
                <div class="loader-inner">
                    <div class="loader-line-wrap">
                        <div class="loader-line"></div>
                    </div>
                    <div class="loader-line-wrap">
                        <div class="loader-line"></div>
                    </div>
                    <div class="loader-line-wrap">
                        <div class="loader-line"></div>
                    </div>
                    <div class="loader-line-wrap">
                        <div class="loader-line"></div>
                    </div>
                    <div class="loader-line-wrap">
                        <div class="loader-line"></div>
                    </div>
                </div>
            </div>
            )} 
            <div class="head">
            <h1>Generate SQL from Text</h1>
            <h4>Improve your SQL skills and save time using LLM's by generating optimized SQL queries effortlessly!</h4>
            </div>
            <style>
@import url('https://fonts.googleapis.com/css2?family=Josefin+Sans:ital,wght@0,100..700;1,100..700&display=swap');
</style>
            <form onSubmit={handleSubmit}>
            <h3>Upload CSV</h3>
                <div style={{
                    display: 'flex'
                }}>
                    <label>
                        <input type="file" required onChange={handleFileChange} />
                    </label>
                    <button 
                    type="button" 
                    onClick={handleShowDetails} 
                    disabled={!file} // Disable button if no file is selected
                >
                    Show Details
                </button>
                </div>
                <div>
                    <input placeholder='Question' type="text" required value={question} onChange={handleQuestionChange} />
                    <button type="submit">Submit</button>
                </div>
            </form>
            {showDetails && (
                <div className="csv-preview">
                    <div className="columns">
                        <h2 className='tt'>Columns</h2>
                        <ul>
                            {csvData.columns.map((col, index) => (
                                <li key={index}>{col}</li>
                            ))}
                        </ul>
                    </div>
                    <div className="table-container">
                        <h2 className='tt'>Preview</h2>
                        <table>
                            <thead>
                                <tr>
                                    {csvData.columns.map((col, index) => (
                                        <th key={index}>{col}</th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {csvData.rows.map((row, rowIndex) => (
                                    <tr key={rowIndex}>
                                        {row.map((cell, cellIndex) => (
                                            <td key={cellIndex}>{cell}</td>
                                        ))}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
            {query && (
                <div className="result-box">
                    <h2 className='tt'>Generated SQL Query:</h2>
                    <pre>{query}</pre>
                </div>
            )}
            {result && result.length > 0 && (
                <div className="result-box">
                    <h2 className='tt'>Query Result:</h2>
                    <table>
                        <thead>
                            <tr>
                                {Object.keys(result[0]).map((key) => (
                                    <th key={key}>{key}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {result.map((row, rowIndex) => (
                                <tr key={rowIndex}>
                                    {Object.keys(row).map((key) => (
                                        <td key={key}>{row[key]}</td>
                                    ))}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
            {plots.length > 0 && (
                <div className='plot-box'>
                    <h2 className='tt'>Generated Plots:</h2>
                    {plots.map((plot, index) => (
                        <img key={index} src={`http://localhost:5000/${plot}`} alt={`Plot ${index}`} />
                    ))}
                </div>
            )}
            {error && (
                <div className="error">
                    <h2 className='tt'>Error:</h2>
                    <pre>{JSON.stringify(error, null, 2)}</pre>
                </div>
            )}
            <div className='theme-toggle-div'>
            <button 
                className="theme-toggle" 
                onClick={toggleTheme} 
                style={{ position: 'absolute', bottom: '20px', right: '20px', height: '80px', borderRadius: '50%', width: '80px'}} // Top right corner
            >
                {isDarkMode ? <img className='theme-img' src={sun} alt=''></img> : <img className='theme-img' src={moon} alt=''></img>}
            </button>
            </div>
        </div>
    );
}

export default App;