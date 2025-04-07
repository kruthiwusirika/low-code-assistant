#!/bin/bash
# Script to rename the project from low-code-assistant to llm-coding-assistant

# Source and target directories
SOURCE_DIR="/Users/kruthiwusirika/Desktop/Project/low_code_assistant"
TARGET_DIR="/Users/kruthiwusirika/Desktop/Project/llm-coding-assistant"

# Create target directory structure
mkdir -p "$TARGET_DIR"

# Copy files with directory structure
cp -R "$SOURCE_DIR"/* "$TARGET_DIR"/

# Rename directories in Helm chart
mv "$TARGET_DIR/helm/low-code-assistant" "$TARGET_DIR/helm/llm-coding-assistant" 2>/dev/null || true

# Update references in files
find "$TARGET_DIR" -type f -name "*.py" -o -name "*.md" -o -name "*.yaml" -o -name "*.sh" -o -name "Dockerfile" | 
while read file; do
  # Replace references in file content
  sed -i '' 's/low-code-assistant/llm-coding-assistant/g' "$file"
  sed -i '' 's/low_code_assistant/llm_coding_assistant/g' "$file"
  sed -i '' 's/Low-Code Assistant/LLM Coding Assistant/g' "$file"
  sed -i '' 's/Low Code Assistant/LLM Coding Assistant/g' "$file"
done

echo "Project renamed from low-code-assistant to llm-coding-assistant"
echo "Files copied to $TARGET_DIR"
echo "Please review the changes and update any references that may have been missed."
