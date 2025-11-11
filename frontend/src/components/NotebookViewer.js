import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Box,
  Typography,
  Button,
  IconButton,
  Paper,
  Chip,
  Fade,
  Avatar,
  Tooltip
} from '@mui/material';
import {
  Close as CloseIcon,
  MenuBook as MenuBookIcon,
  ContentCopy as ContentCopyIcon,
  Download as DownloadIcon,
  Fullscreen as FullscreenIcon,
  FullscreenExit as FullscreenExitIcon
} from '@mui/icons-material';

// Simple syntax highlighting for Python code
const highlightPythonCode = (code) => {
  const keywords = ['def', 'class', 'if', 'else', 'elif', 'for', 'while', 'try', 'except', 'finally', 'with', 'as', 'import', 'from', 'return', 'yield', 'break', 'continue', 'pass', 'and', 'or', 'not', 'in', 'is', 'None', 'True', 'False', 'lambda', 'global', 'nonlocal'];
  const builtins = ['print', 'len', 'str', 'int', 'float', 'list', 'dict', 'set', 'tuple', 'range', 'enumerate', 'zip', 'map', 'filter', 'open', 'read', 'write', 'input', 'type', 'isinstance', 'hasattr', 'getattr', 'setattr'];
  
  return code.split('\n').map((line, lineIndex) => {
    // Handle empty lines
    if (line.trim() === '') {
      return <div key={lineIndex}>&nbsp;</div>;
    }
    
    // Handle comment lines
    if (line.trim().startsWith('#')) {
      return (
        <div key={lineIndex} style={{ color: '#6a9955', fontStyle: 'italic' }}>
          {line}
        </div>
      );
    }
    
    // For non-comment lines, apply syntax highlighting
    const parts = [];
    let remaining = line;
    
    // Simple tokenization and highlighting
    const tokens = remaining.split(/(\s+|[()[\]{},.:;=+\-*/<>!&|%]+)/);
    
    tokens.forEach((token, tokenIndex) => {
      if (!token) return;
      
      if (keywords.includes(token.trim())) {
        parts.push(<span key={`${lineIndex}-${tokenIndex}`} style={{ color: '#569cd6', fontWeight: 'bold' }}>{token}</span>);
      } else if (builtins.some(builtin => token.includes(builtin) && token.includes('('))) {
        const highlighted = token.replace(new RegExp(`\\b(${builtins.join('|')})\\b(?=\\()`, 'g'), '<span style="color: #dcdcaa; font-weight: 600;">$1</span>');
        parts.push(<span key={`${lineIndex}-${tokenIndex}`} dangerouslySetInnerHTML={{ __html: highlighted }} />);
      } else if (/^(['"`]).*\1$/.test(token.trim()) || /^(['"`]).*/.test(token) || /.*(['"`])$/.test(token)) {
        parts.push(<span key={`${lineIndex}-${tokenIndex}`} style={{ color: '#ce9178' }}>{token}</span>);
      } else if (/^\d+\.?\d*$/.test(token.trim())) {
        parts.push(<span key={`${lineIndex}-${tokenIndex}`} style={{ color: '#b5cea8' }}>{token}</span>);
      } else if (token.trim() && /^[a-zA-Z_]\w*$/.test(token.trim()) && !keywords.includes(token.trim())) {
        parts.push(<span key={`${lineIndex}-${tokenIndex}`} style={{ color: '#9cdcfe' }}>{token}</span>);
      } else {
        parts.push(<span key={`${lineIndex}-${tokenIndex}`}>{token}</span>);
      }
    });
    
    return (
      <div key={lineIndex} style={{ fontFamily: 'inherit', whiteSpace: 'pre' }}>
        {parts.length > 0 ? parts : line}
      </div>
    );
  });
};

const NotebookViewer = ({ notebook, onClose }) => {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState(null);

  if (!notebook) return null;

  const handleCopyCode = async (code, index) => {
    try {
      await navigator.clipboard.writeText(code);
      setCopiedIndex(index);
      setTimeout(() => setCopiedIndex(null), 2000);
    } catch (err) {
      console.error('Failed to copy code:', err);
    }
  };

  const handleDownload = () => {
    const blob = new Blob([notebook.code], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${notebook.notebook_name || 'notebook'}.py`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  // Display code as a single block
  const displayCode = notebook.code || '';

  return (
    <Dialog
      open={true}
      onClose={onClose}
      maxWidth={isFullscreen ? false : 'lg'}
      fullWidth
      fullScreen={isFullscreen}
      sx={{
        '& .MuiDialog-paper': {
          borderRadius: isFullscreen ? 0 : 3,
          maxHeight: isFullscreen ? '100vh' : '90vh',
          bgcolor: '#fafafa',
          overflow: 'hidden',
        },
      }}
      TransitionComponent={Fade}
      TransitionProps={{
        timeout: 300,
      }}
    >
      <DialogTitle
        sx={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          py: 2,
          px: 3,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Avatar
            sx={{
              width: 32,
              height: 32,
              bgcolor: 'rgba(255, 255, 255, 0.2)',
              backdropFilter: 'blur(10px)',
            }}
          >
            <MenuBookIcon sx={{ fontSize: 18, color: 'white' }} />
          </Avatar>
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 600, fontSize: '1.1rem' }}>
              {notebook.notebook_name || 'Notebook'}
            </Typography>
            {notebook.layer && (
              <Chip
                label={notebook.layer}
                size="small"
                sx={{
                  bgcolor: 'rgba(255, 255, 255, 0.2)',
                  color: 'white',
                  fontSize: '0.7rem',
                  height: 20,
                  mt: 0.5,
                  fontWeight: 600,
                }}
              />
            )}
          </Box>
        </Box>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Tooltip title="Copy All Code">
            <IconButton
              onClick={() => handleCopyCode(notebook.code, 'all')}
              sx={{ color: 'white', '&:hover': { bgcolor: 'rgba(255, 255, 255, 0.1)' } }}
            >
              <ContentCopyIcon sx={{ fontSize: 20 }} />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Download Notebook">
            <IconButton
              onClick={handleDownload}
              sx={{ color: 'white', '&:hover': { bgcolor: 'rgba(255, 255, 255, 0.1)' } }}
            >
              <DownloadIcon sx={{ fontSize: 20 }} />
            </IconButton>
          </Tooltip>
          
          <Tooltip title={isFullscreen ? "Exit Fullscreen" : "Fullscreen"}>
            <IconButton
              onClick={toggleFullscreen}
              sx={{ color: 'white', '&:hover': { bgcolor: 'rgba(255, 255, 255, 0.1)' } }}
            >
              {isFullscreen ? <FullscreenExitIcon sx={{ fontSize: 20 }} /> : <FullscreenIcon sx={{ fontSize: 20 }} />}
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Close">
            <IconButton
              onClick={onClose}
              sx={{ color: 'white', '&:hover': { bgcolor: 'rgba(255, 255, 255, 0.1)' } }}
            >
              <CloseIcon sx={{ fontSize: 20 }} />
            </IconButton>
          </Tooltip>
        </Box>
      </DialogTitle>

      <DialogContent
        sx={{
          p: 0,
          bgcolor: '#fafafa',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <Box
          sx={{
            flex: 1,
            overflow: 'auto',
            '&::-webkit-scrollbar': {
              width: '6px',
            },
            '&::-webkit-scrollbar-track': {
              background: 'transparent',
            },
            '&::-webkit-scrollbar-thumb': {
              background: 'rgba(102, 126, 234, 0.3)',
              borderRadius: '3px',
              '&:hover': {
                background: 'rgba(102, 126, 234, 0.5)',
              },
            },
          }}
        >
          {notebook.description && (
            <Paper
              elevation={0}
              sx={{
                m: 2,
                p: 2,
                borderRadius: 2,
                border: '1px solid rgba(102, 126, 234, 0.12)',
                background: 'linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(248,250,252,0.9) 100%)',
              }}
            >
              <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                {notebook.description}
              </Typography>
            </Paper>
          )}

          <Box sx={{ p: 2, pt: notebook.description ? 0 : 2 }}>
            <Paper
              elevation={0}
              sx={{
                mb: 2,
                borderRadius: 2,
                border: '1px solid rgba(102, 126, 234, 0.08)',
                overflow: 'hidden',
                bgcolor: 'white',
                transition: 'all 0.2s ease-in-out',
                '&:hover': {
                  boxShadow: '0 4px 12px rgba(102, 126, 234, 0.1)',
                  transform: 'translateY(-1px)',
                },
              }}
            >
              {/* Header */}
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  px: 2,
                  py: 1,
                  bgcolor: 'rgba(59, 130, 246, 0.05)',
                  borderBottom: '1px solid rgba(0,0,0,0.05)',
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Avatar
                    sx={{
                      width: 20,
                      height: 20,
                      bgcolor: '#3b82f6',
                    }}
                  >
                    <Typography sx={{ fontSize: '0.65rem', fontWeight: 'bold', color: 'white' }}>
                      C
                    </Typography>
                  </Avatar>
                  <Typography variant="caption" sx={{ fontWeight: 600, fontSize: '0.75rem' }}>
                    Notebook Code
                  </Typography>
                </Box>
                
                <Tooltip title={copiedIndex === 'notebook' ? "Copied!" : "Copy Code"}>
                  <IconButton
                    onClick={() => handleCopyCode(displayCode, 'notebook')}
                    size="small"
                    sx={{
                      color: copiedIndex === 'notebook' ? 'success.main' : 'text.secondary',
                      '&:hover': { bgcolor: 'rgba(102, 126, 234, 0.1)' },
                      transition: 'all 0.2s ease-in-out',
                    }}
                  >
                    <ContentCopyIcon sx={{ fontSize: 14 }} />
                  </IconButton>
                </Tooltip>
              </Box>

              {/* Code Content */}
              <Box
                sx={{
                  bgcolor: '#1e1e1e',
                  color: '#d4d4d4',
                  fontFamily: '"Fira Code", "Monaco", "Menlo", "Consolas", monospace',
                  fontSize: '0.875rem',
                  lineHeight: 1.5,
                  maxHeight: '60vh',
                  overflow: 'auto',
                  position: 'relative',
                  '&::-webkit-scrollbar': {
                    width: '8px',
                    height: '8px',
                  },
                  '&::-webkit-scrollbar-track': {
                    background: '#2d2d2d',
                  },
                  '&::-webkit-scrollbar-thumb': {
                    background: '#555',
                    borderRadius: '4px',
                    '&:hover': {
                      background: '#666',
                    },
                  },
                }}
              >
                <Box
                  component="pre"
                  sx={{
                    margin: 0,
                    padding: '16px',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: 2,
                  }}
                >
                  {/* Line Numbers */}
                  <Box
                    sx={{
                      color: '#858585',
                      fontSize: '0.8rem',
                      textAlign: 'right',
                      minWidth: '3em',
                      paddingRight: '1em',
                      borderRight: '1px solid #444',
                      userSelect: 'none',
                      flexShrink: 0,
                    }}
                  >
                    {displayCode.split('\n').map((_, lineIndex) => (
                      <Box key={lineIndex} sx={{ lineHeight: 1.5 }}>
                        {lineIndex + 1}
                      </Box>
                    ))}
                  </Box>
                  
                  {/* Code Content */}
                  <Box
                    component="code"
                    sx={{
                      flex: 1,
                      color: 'inherit',
                      fontFamily: 'inherit',
                      fontSize: 'inherit',
                      lineHeight: 'inherit',
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                    }}
                  >
                    <Box sx={{ fontFamily: 'inherit' }}>
                      {highlightPythonCode(displayCode)}
                    </Box>
                  </Box>
                </Box>
              </Box>
            </Paper>
          </Box>
        </Box>
      </DialogContent>

      {!isFullscreen && (
        <DialogActions
          sx={{
            px: 3,
            py: 2,
            bgcolor: 'white',
            borderTop: '1px solid rgba(0,0,0,0.06)',
            gap: 1,
          }}
        >
          <Button
            onClick={handleDownload}
            variant="outlined"
            startIcon={<DownloadIcon />}
            sx={{
              borderColor: 'rgba(102, 126, 234, 0.3)',
              color: '#667eea',
              borderRadius: 2,
              textTransform: 'none',
              fontWeight: 600,
              '&:hover': {
                borderColor: '#667eea',
                bgcolor: 'rgba(102, 126, 234, 0.04)',
              },
            }}
          >
            Download
          </Button>
          
          <Button
            onClick={() => handleCopyCode(notebook.code, 'all')}
            variant="outlined"
            startIcon={<ContentCopyIcon />}
            sx={{
              borderColor: 'rgba(102, 126, 234, 0.3)',
              color: '#667eea',
              borderRadius: 2,
              textTransform: 'none',
              fontWeight: 600,
              '&:hover': {
                borderColor: '#667eea',
                bgcolor: 'rgba(102, 126, 234, 0.04)',
              },
            }}
          >
            Copy All
          </Button>
          
          <Button
            onClick={onClose}
            variant="contained"
            sx={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              borderRadius: 2,
              textTransform: 'none',
              fontWeight: 600,
              px: 3,
              '&:hover': {
                background: 'linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%)',
                transform: 'translateY(-1px)',
              },
              transition: 'all 0.2s ease-in-out',
            }}
          >
            Close
          </Button>
        </DialogActions>
      )}
    </Dialog>
  );
};

export default NotebookViewer;
