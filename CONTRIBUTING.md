# Contributing to Manufacturing Systems Security Framework

Thank you for your interest in contributing to this research project! This document provides guidelines for collaboration and contribution.

## Code of Conduct

### Research Ethics

All contributors must adhere to ethical research practices:

1. **Responsible Use**: This framework is for research and education only
2. **Authorized Testing**: Only test on systems you own or have explicit permission to test
3. **Disclosure**: Follow responsible disclosure practices for any vulnerabilities discovered
4. **Safety First**: Prioritize physical safety when testing with hardware
5. **Transparency**: Document all experiments and methodologies clearly

## Ways to Contribute

### 1. Research Contributions
- Novel attack vectors or scenarios
- Defense mechanism implementations
- Experimental results and analysis
- Case studies from real-world testing

### 2. Code Contributions
- Bug fixes
- Feature implementations
- Performance improvements
- Test coverage expansion
- Documentation improvements

### 3. Documentation
- Tutorial creation
- API documentation
- Architecture diagrams
- Experiment protocols
- Best practices guides

### 4. Testing and Validation
- Reproduce existing experiments
- Validate results across different environments
- Report issues and edge cases
- Suggest improvements

## Getting Started

### For Research Collaborators

1. **Contact the team** to discuss your research interests
2. **Review existing work** in `docs/` and published papers
3. **Set up your environment** following `docs/GETTING_STARTED.md`
4. **Propose experiments** using the experiment template

### For Code Contributors

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes** following our coding standards
4. **Test thoroughly** in your local environment
5. **Submit a pull request** with clear description

## Development Guidelines

### Python Code Standards

- **Style**: Follow PEP 8 guidelines
- **Type Hints**: Use type hints for function signatures
- **Docstrings**: Include docstrings for all public functions/classes
- **Comments**: Comment complex logic and algorithms

Example:
```python
def analyze_attack_success(
    commands: List[str],
    modifications: List[str],
    threshold: float = 0.95
) -> Dict[str, Any]:
    """
    Analyze attack success rate based on command modifications.
    
    Args:
        commands: List of original G-code commands
        modifications: List of modified commands
        threshold: Success threshold (default: 0.95)
    
    Returns:
        Dictionary containing success metrics
    """
    # Implementation here
    pass
```

### Git Commit Messages

Use clear, descriptive commit messages:

```
[Type] Brief description (50 chars or less)

Detailed explanation of what changed and why (if needed).

- Bullet points for multiple changes
- Reference issues: Fixes #123
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions/changes
- `refactor`: Code refactoring
- `perf`: Performance improvements

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation
- `experiment/name` - Experimental branches

## Pull Request Process

1. **Update documentation** if you change APIs or add features
2. **Add tests** for new functionality
3. **Ensure all tests pass** before submitting
4. **Update CHANGELOG.md** with your changes
5. **Link related issues** in the PR description
6. **Wait for review** from maintainers

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Commit messages are clear
- [ ] No sensitive data in commits
- [ ] Experiment results are reproducible

## Experiment Contributions

### Experiment Submission Format

When contributing experimental results:

1. **Configuration File**: Include complete experiment configuration
2. **Raw Data**: Provide raw data files in specified formats
3. **Analysis Scripts**: Include scripts used for analysis
4. **Results Summary**: Write a summary of findings
5. **Reproducibility**: Document exact steps to reproduce

### Experiment Template

```json
{
  "experiment_id": "YYYYMMDD_researcher_name",
  "title": "Descriptive Title",
  "hypothesis": "What you're testing",
  "methodology": "Brief description of approach",
  "configuration": {
    "network": {},
    "attack": {},
    "defense": {}
  },
  "results": {
    "success_rate": 0.0,
    "detection_rate": 0.0,
    "metrics": {}
  },
  "conclusion": "Summary of findings",
  "reproducibility": "Steps to reproduce"
}
```

## Testing Requirements

### Unit Tests

- Write tests for new functions
- Use pytest framework
- Aim for >80% code coverage

```python
def test_attack_simulator():
    """Test attack simulator initialization"""
    simulator = GCodeAttackSimulator('192.168.1.1', 8080)
    assert simulator.cnc_ip == '192.168.1.1'
    assert simulator.cnc_port == 8080
```

### Integration Tests

- Test complete workflows
- Verify component interactions
- Test with Docker infrastructure

### Experiment Validation

- Reproduce key experiments
- Verify results match published data
- Document any discrepancies

## Documentation Standards

### Code Documentation

- Docstrings for all public APIs
- Inline comments for complex logic
- Type hints for function signatures

### Research Documentation

- Clear methodology descriptions
- Statistical analysis details
- Limitations and assumptions
- Future work suggestions

### Markdown Guidelines

- Use headers hierarchically (# ## ### etc.)
- Include code examples where relevant
- Link to related documentation
- Keep line length reasonable (<100 chars preferred)

## Security and Privacy

### Reporting Security Issues

**DO NOT** open public issues for security vulnerabilities.

Instead:
1. Email the maintainers directly
2. Provide detailed description
3. Include proof-of-concept if possible
4. Wait for acknowledgment before disclosure

### Data Privacy

- Never commit sensitive information
- Use `.gitignore` for credentials
- Anonymize any real-world data
- Follow institutional IRB guidelines

## Community and Communication

### Channels

- **GitHub Issues**: Bug reports, feature requests
- **Pull Requests**: Code contributions
- **Discussions**: General questions, ideas
- **Email**: Research collaboration, security issues

### Response Times

- **Critical bugs**: Within 24 hours
- **General issues**: Within 1 week
- **Pull requests**: Within 2 weeks
- **Research inquiries**: Within 1 week

## Recognition

Contributors will be acknowledged in:
- CONTRIBUTORS.md file
- Project documentation
- Academic publications (as appropriate)
- Release notes

## License

By contributing, you agree that your contributions will be licensed under the MIT License as specified in LICENSE file.

## Questions?

If you have questions about contributing:
1. Check existing documentation
2. Search closed issues
3. Open a new discussion
4. Email the maintainers

---

Thank you for contributing to advancing manufacturing systems security research!

**Last Updated**: November 10, 2025  
**Version**: 1.0.0
