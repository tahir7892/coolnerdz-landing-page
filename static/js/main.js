    function updatePill(tab) {
      const pill = tab.parentElement.querySelector('.sliding-pill');
      if (!pill) return;
      pill.style.width = tab.offsetWidth + 'px';
      pill.style.height = tab.offsetHeight + 'px';
      pill.style.left = tab.offsetLeft + 'px';
      pill.style.top = tab.offsetTop + 'px';
    }

    function switchTab(clickedTab, targetId) {
      document.querySelectorAll('.role-tab').forEach(t => t.classList.remove('active'));
      clickedTab.classList.add('active');
      
      updatePill(clickedTab);
      
      document.querySelectorAll('.role-stage').forEach(s => s.classList.add('hidden'));
      document.getElementById(targetId).classList.remove('hidden');
    }

    window.addEventListener('DOMContentLoaded', () => {
      const activeTab = document.querySelector('.role-tab.active');
      if (activeTab) {
        setTimeout(() => updatePill(activeTab), 50);
      }
    });

    window.addEventListener('resize', () => {
      const activeTab = document.querySelector('.role-tab.active');
      if (activeTab) {
        updatePill(activeTab);
      }
    });

    // Intersection Observer for Navbar active state
    window.addEventListener('DOMContentLoaded', () => {
      const sections = document.querySelectorAll('section[id]');
      const navLinks = document.querySelectorAll('.nav-links a');
      
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            navLinks.forEach(link => {
              link.classList.remove('active');
              if (link.getAttribute('href') === '#' + entry.target.id) {
                link.classList.add('active');
              }
            });
          }
        });
      }, {
        rootMargin: '-20% 0px -60% 0px',
        threshold: 0
      });
      
      sections.forEach(section => observer.observe(section));
    });

    let waitlistMessageTimeout;
    let waitlistIsSubmitting = false;

    function attachWaitlistHandler() {
      const waitlistForm = document.getElementById('waitlist-form');

      if (!waitlistForm || waitlistForm.dataset.bound === 'true') {
        return;
      }

      waitlistForm.dataset.bound = 'true';
      waitlistForm.addEventListener('submit', submitWaitlist);
    }

    async function submitWaitlist(e) {
      if (e) {
        e.preventDefault();
        e.stopPropagation();
      }

      if (waitlistIsSubmitting) {
        return false;
      }

      const waitlistForm = document.getElementById('waitlist-form');
      const waitlistMessage = document.getElementById('waitlist-message');
      const submitButton = waitlistForm ? waitlistForm.querySelector('button[type="submit"]') : null;

      if (waitlistForm && waitlistMessage) {
          const emailInput = document.getElementById('waitlist-email');
          const roleSelect = document.getElementById('waitlist-role');
          
          const email = emailInput.value.trim();
          const role = roleSelect.value;

          // Clear previous messages
          waitlistMessage.style.display = 'none';
          waitlistMessage.className = '';

          // Validate
          if (!email || !role) {
            showMessage('Please provide a valid email and select a role.', 'error');
            return false;
          }

          waitlistIsSubmitting = true;

          if (submitButton) {
            submitButton.disabled = true;
            submitButton.textContent = 'Joining...';
          }

          try {
            const csrfInput = waitlistForm.querySelector('input[name="csrfmiddlewaretoken"]');
            const response = await fetch('/api/waitlist', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': csrfInput ? csrfInput.value : ''
            },
            body: JSON.stringify({ email, role })
            });
            const data = await response.json();
            if (response.ok) {
              showMessage(data.message || 'You have successfully joined the waitlist!', 'success');
              waitlistForm.reset();
            } else {
              showMessage(data.error || 'An error occurred. Please try again later.', 'error');
            }
          } catch (err) {
            console.error('Error sending waitlist entry:', err);
            showMessage('A network error occurred. Please try again later.', 'error');
          } finally {
            waitlistIsSubmitting = false;
            if (submitButton) {
              submitButton.disabled = false;
              submitButton.textContent = 'Join waitlist';
            }
          }
      }

      function showMessage(msg, type) {
        waitlistMessage.textContent = msg;
        waitlistMessage.style.display = 'block';
        if (type === 'success') {
          waitlistMessage.style.backgroundColor = '#bee8d4'; // var(--mint)
          waitlistMessage.style.color = '#092d29'; // var(--pine)
          waitlistMessage.style.border = '1px solid #70bea0';
        } else {
          waitlistMessage.style.backgroundColor = '#ffc7b8'; // var(--rose)
          waitlistMessage.style.color = '#101615'; // var(--ink)
          waitlistMessage.style.border = '1px solid #d96f5f';
        }
        
        clearTimeout(waitlistMessageTimeout);
        waitlistMessageTimeout = setTimeout(() => {
          waitlistMessage.style.display = 'none';
        }, 3000);
      }

      return false;
    }

    window.submitWaitlist = submitWaitlist;
    attachWaitlistHandler();
    document.addEventListener('DOMContentLoaded', attachWaitlistHandler);
