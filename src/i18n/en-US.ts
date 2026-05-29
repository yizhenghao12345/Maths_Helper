import { zhCN } from './zh-CN'

export const enUS: typeof zhCN = {
  home: {
    appName: 'Math Thinking Trainer',
    title: 'Say Goodbye to "Understand But Cannot Solve"',
    subtitle: 'Develop mathematical logical thinking from the ground up through visual thinking nodes and interactive guidance',
    startButton: 'Get Started',
    features: [
      {
        title: 'Visual Mind Map',
        description: 'Visualize the problem-solving process so you can see every step of the thinking logic',
      },
      {
        title: 'AI-Guided Deduction',
        description: 'Through Socratic questioning, guide you to think independently and build problem-solving skills',
      },
      {
        title: 'Exploration-Based Learning',
        description: 'Allow wrong turns with gentle guidance when mistakes happen, helping you find the right direction',
      },
    ],
  },
  input: {
    backHome: 'Back to Home',
    title: 'Input Problem',
    subtitle: 'Enter the math problem you want to solve, and the system will generate a thinking deduction map for you',
    placeholder: 'e.g., Solve the equation 2x + 5 = 13, find the value of x',
    uploadImage: 'Upload Image',
    recognizeImage: 'Recognize Text from Image',
    recognizing: 'Recognizing...',
    preview: 'Preview',
    startDeduction: 'Start Deduction',
    parsing: 'Parsing...',
    submitError: 'Submission failed, please retry',
    pleaseInput: 'Please enter the problem content',
    selectImageError: 'Please select an image file',
    noTextRecognized: 'No text content recognized',
    recognizeError: 'Image recognition failed, please retry',
    charCount: 'chars',
    firstQuestion: 'Looking at this problem, what do you think the first step should be?',
    firstOptions: [
      'A. Carefully analyze the known conditions',
      'B. Try calculating directly',
      'C. Skip the analysis',
      'D. No thinking',
    ],
  },
  deduction: {
    back: 'Back',
    title: 'Thinking Deduction',
    thinkingGuide: 'Thinking Guide',
    followThinking: 'Follow the questions step by step',
    solutionTitle: 'Complete Solution',
    completedTitle: 'Deduction Complete!',
    completedDesc: 'Congratulations on completing the thinking deduction for this problem',
    nextProblem: 'Try Another Problem',
    submitError: 'Submission failed, please retry',
  },
  questionPanel: {
    successIcon: '✓',
    warning: '⚠',
  },
  common: {
    languageSwitch: '中文',
  },
}
