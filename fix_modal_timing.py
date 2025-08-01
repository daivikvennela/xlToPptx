#!/usr/bin/env python3

def fix_modal_timing():
    """Move modal creation to happen immediately when page loads"""
    
    # Read the file
    with open('templates/index.html', 'r') as f:
        content = f.read()
    
    # Define the modal creation code to add at the beginning
    modal_creation_code = '''
        // Create Exhibit A modal immediately when page loads
        function createExhibitAModal() {
          if (!document.getElementById("exhibitAModal")) {
            const modal = document.createElement("div");
            modal.id = "exhibitAModal";
            modal.style = "display:none; position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(0,0,0,0.7); z-index:10000; align-items:center; justify-content:center;";
            modal.innerHTML = `
              <div style="background:#232347; color:#e2e8f0; border-radius:12px; padding:2rem; min-width:800px; max-width:95vw; max-height:90vh; overflow-y:auto; position:relative; box-shadow:0 8px 32px #0008;">
                <button id="closeExhibitAModal" style="position:absolute; top:1rem; right:1rem; background:none; border:none; color:#ff6b6b; font-size:1.5rem; cursor:pointer;">&times;</button>
                <h2 style="color:#00bfff; margin-bottom:1.5rem;">Generate Exhibit A</h2>
                <div id="parcelListContainer" style="margin-bottom:1.5rem;"></div>
                <button id="addParcelBtn" class="secondary-btn" style="margin-bottom:1rem;">Add Parcel</button>
                <div style="text-align:center; margin-top:1.5rem;">
                  <button id="modalGenerateExhibitABtn" class="submit-btn" style="margin-right:1rem;">Generate Exhibit A</button>
                  <button id="cancelExhibitABtn" class="secondary-btn">Cancel</button>
                </div>
              </div>
            `;
            document.body.appendChild(modal);
            console.log("Exhibit A modal created successfully");
          }
        }
        
        // Create modal immediately
        createExhibitAModal();
'''
    
    # Find where to insert the modal creation (after the initial script setup)
    insert_marker = "        // Add initial pair"
    pos = content.find(insert_marker)
    
    if pos != -1:
        # Insert modal creation before the button creation
        new_content = content[:pos] + modal_creation_code + content[pos:]
        
        # Write the updated content
        with open('templates/index.html', 'w') as f:
            f.write(new_content)
        
        print("Successfully added modal creation before button creation")
        return True
    else:
        print("Could not find insert marker")
        return False

if __name__ == "__main__":
    fix_modal_timing()
