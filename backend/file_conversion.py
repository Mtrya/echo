from typing import List
from pathlib import Path

class FileProcessor:
    """Mock implementation: will switch to LLM processing later."""
    
    def __init__(self):
        self.supported_formats = [".docx", ".txt"]
    
    def extract_text_from_docx(self, file_content: bytes) -> str:
        """Extract text from DOCX file"""
        try:
            # This would require python-docx library
            # For now, return a mock implementation
            return "DOCX processing requires python-docx library"
        except Exception as e:
            return f"Error processing DOCX: {str(e)}"
    
    def extract_text_from_txt(self, file_content: bytes) -> str:
        """Extract text from TXT file"""
        try:
            return file_content.decode('utf-8')
        except Exception as e:
            return f"Error processing TXT: {str(e)}"
    
    def parse_questions_from_text(self, text: str) -> List[dict]:
        """Parse questions from extracted text"""
        # Simple question parsing - can be enhanced
        questions = []
        lines = text.split('\n')
        
        current_question = {}
        for line in lines:
            line = line.strip()
            if line.startswith(('Q:', 'Question:', '1.', '2.', '3.', '4.', '5.')):
                if current_question:
                    questions.append(current_question)
                current_question = {
                    'text': line,
                    'type': 'multiple_choice',
                    'options': [],
                    'reference_answer': None
                }
            elif line.startswith(('A:', 'B:', 'C:', 'D:')):
                option = line[2:].strip()
                current_question['options'].append(option)
        
        if current_question:
            questions.append(current_question)
        
        return questions
    
    def process_file(self, filename: str, file_content: bytes) -> dict:
        """Process a file and extract questions"""
        file_path = Path(filename)
        file_extension = file_path.suffix.lower()
        
        if file_extension not in self.supported_formats:
            return {
                'success': False,
                'error': f'Unsupported file format: {file_extension}',
                'questions': []
            }
        
        # Extract text based on file type
        if file_extension == '.docx':
            text = self.extract_text_from_docx(file_content)
        elif file_extension == '.txt':
            text = self.extract_text_from_txt(file_content)
        else:
            return {
                'success': False,
                'error': f'Unsupported file format: {file_extension}',
                'questions': []
            }
        
        # Parse questions from text
        questions = self.parse_questions_from_text(text)
        
        return {
            'success': True,
            'text': text,
            'questions': questions,
            'question_count': len(questions)
        }
    
    def convert_to_yaml(self, questions: List[dict], title: str = "Converted Exam") -> str:
        """Convert parsed questions to YAML format"""
        import yaml
        
        exam_data = {
            'exam': {
                'title': title,
                'description': f'Exam converted from file with {len(questions)} questions',
                'questions': questions
            }
        }
        
        return yaml.dump(exam_data, default_flow_style=False, allow_unicode=True)
    
    def save_as_yaml(self, questions: List[dict], output_filename: str, title: str = "Converted Exam") -> bool:
        """Save converted questions as YAML file"""
        try:
            yaml_content = self.convert_to_yaml(questions, title)
            
            # Ensure output directory exists
            output_path = Path(output_filename)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(yaml_content)
            
            return True
        except Exception as e:
            print(f"Error saving YAML file: {e}")
            return False

if __name__ == "__main__":
    # Test the FileProcessor
    print("Testing File Processor...")
    
    file_processor = FileProcessor()
    
    # Test text extraction from TXT
    print("\nTesting TXT processing...")
    sample_text = b"""Q: What is 2+2?
A: 4
B: 5
C: 6
D: 7

Question: What is your favorite color?
A: Red
B: Blue
C: Green
D: Yellow"""
    
    txt_result = file_processor.process_file("sample.txt", sample_text)
    print(f"Success: {txt_result['success']}")
    print(f"Question count: {txt_result['question_count']}")
    print(f"Questions: {txt_result['questions']}")
    
    # Test YAML conversion
    print("\nTesting YAML conversion...")
    if txt_result['success']:
        yaml_content = file_processor.convert_to_yaml(txt_result['questions'], "Sample Test")
        print("Generated YAML:")
        print(yaml_content)
        
        # Test saving YAML
        save_success = file_processor.save_as_yaml(txt_result['questions'], "exams/converted_test.yaml")
        print(f"YAML saved successfully: {save_success}")
    
    # Test DOCX processing (mock)
    print("\nTesting DOCX processing...")
    docx_result = file_processor.process_file("sample.docx", b"mock docx content")
    print(f"Success: {docx_result['success']}")
    print(f"Text: {docx_result['text']}")
    
    print("\nFile Processor tests completed!")