import re

with open('app/templates/home.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Define the new content
new_hero = '''<!-- VIEW 1: HOME HERO VIEW -->
<div id="home-hero-view" class="flex-1 flex flex-col items-center justify-center px-6 relative w-full max-w-5xl mx-auto min-h-[70vh]">
    <!-- Vibrant Animated Ambient Background Elements -->
    <div class="fixed inset-0 pointer-events-none overflow-hidden z-[-1]">
        <div class="absolute -top-[10%] -right-[5%] w-[50vw] h-[50vw] rounded-full bg-gradient-to-br from-[#4a7c59]/20 to-[#78a886]/20 blur-[100px] opacity-70 animate-[pulse_8s_ease-in-out_infinite] mix-blend-multiply"></div>
        <div class="absolute top-[20%] -left-[10%] w-[40vw] h-[40vw] rounded-full bg-gradient-to-tr from-[#c4a66a]/20 to-[#f0e8db]/10 blur-[100px] opacity-60 animate-[pulse_10s_ease-in-out_infinite_reverse] mix-blend-multiply"></div>
    </div>

    <div class="text-center mb-16 max-w-2xl mx-auto mt-8">
        <h1 class="font-headline text-5xl md:text-7xl text-[#2e3230] mb-6 font-black tracking-tight drop-shadow-sm">Discover Nature</h1>
        <p class="font-body text-lg md:text-xl text-[#4a4e4a] leading-relaxed max-w-lg mx-auto font-medium">Identify plants, trees, and flowers instantly. Connect with your environment through the lens of AI.</p>
    </div>

    <!-- The Massive Scanner Button Assembly -->
    <div class="relative flex items-center justify-center group mb-16 cursor-pointer w-full max-w-[280px] md:max-w-[340px] aspect-square" onclick="openLaboratory('camera')">
        <!-- Static "Pulse" Rings -->
        <div class="absolute inset-[-25%] rounded-full bg-[#4a7c59]/5 border border-[#4a7c59]/10 flex items-center justify-center scale-100 transition-transform duration-700 group-hover:scale-110">
            <div class="absolute inset-[15%] rounded-full bg-[#4a7c59]/10 border border-[#4a7c59]/20 scale-100 transition-transform duration-500 group-hover:scale-105"></div>
        </div>
        <!-- Core Button Container -->
        <button class="relative w-[85%] h-[85%] bg-gradient-to-b from-[#5a8c69] to-[#3a6c49] rounded-[3rem] shadow-[0_20px_50px_rgba(74,124,89,0.4)] flex flex-col items-center justify-center gap-5 transition-all duration-300 active:scale-95 group-hover:shadow-[0_30px_60px_rgba(74,124,89,0.6)] overflow-hidden z-10 border-t border-white/20 border-b border-black/20 group-hover:-translate-y-2">
            <!-- Inner soft highlight for depth -->
            <div class="absolute inset-0 bg-gradient-to-br from-white/30 to-transparent pointer-events-none rounded-[3rem]"></div>
            
            <!-- Animated glowing center -->
            <div class="absolute inset-0 bg-white/0 group-hover:bg-white/10 transition-colors duration-500"></div>
            
            <!-- Icon -->
            <div class="bg-white/10 p-6 rounded-[1.5rem] mb-2 backdrop-blur-sm border border-white/10 shadow-inner">
                <span class="material-symbols-outlined text-6xl text-white font-light drop-shadow-md" style="font-variation-settings: 'wght' 200;">document_scanner</span>
            </div>
            <!-- Primary Call to Action -->
            <span class="font-headline text-2xl tracking-tight text-white font-bold px-4 text-center drop-shadow-md">
                Tap to Scan
            </span>
        </button>
    </div>

    <!-- Secondary Actions -->
    <div class="flex flex-col sm:flex-row items-center gap-6">
        <button onclick="document.getElementById('single-file-input').click()" class="flex items-center gap-3 px-8 py-4 bg-white/80 backdrop-blur-md rounded-2xl text-[#4a7c59] font-body text-base font-bold border border-white hover:bg-white transition-all active:scale-95 shadow-[0_8px_30px_rgba(46,50,48,0.06)] hover:shadow-[0_12px_40px_rgba(46,50,48,0.12)] hover:-translate-y-1">
            <span class="material-symbols-outlined text-2xl">photo_library</span>
            Upload from Gallery
        </button>
        <button onclick="document.getElementById('batch-file-input').click()" class="flex items-center gap-3 px-8 py-4 bg-transparent rounded-2xl text-[#4a7c59] font-body text-base font-bold border-2 border-[#4a7c59]/20 hover:border-[#4a7c59]/40 hover:bg-[#4a7c59]/5 transition-all active:scale-95 hover:-translate-y-1">
            <span class="material-symbols-outlined text-2xl">collections</span>
            Batch Analysis
        </button>
    </div>

    <!-- Hidden Upload Forms -->
    <form id="single-upload-form" action="/upload/" method="POST" enctype="multipart/form-data" class="hidden">
        <input type="file" id="single-file-input" name="img" accept="image/png, image/jpeg, image/jpg" />
    </form>
    <form id="batch-upload-form" action="/batch/" method="POST" enctype="multipart/form-data" class="hidden">
        <input type="file" id="batch-file-input" name="images" multiple accept="image/png, image/jpeg, image/jpg" onchange="document.getElementById('batch-upload-form').submit();" />
    </form>
</div>

<!-- Recent Discoveries -->
<section class="hidden lg:block px-6 py-8 max-w-5xl mx-auto w-full mt-12 mb-12">
    <div class="flex items-center justify-between mb-8">
        <h2 class="font-headline text-2xl text-[#2e3230] font-bold flex items-center gap-3">
            <span class="material-symbols-outlined text-[#4a7c59] bg-[#4a7c59]/10 p-2 rounded-xl">eco</span>
            Recent Discoveries
        </h2>
        <a href="/history" class="text-sm font-bold text-[#4a7c59] hover:text-[#3a6c49] flex items-center gap-1 transition-colors">View All <span class="material-symbols-outlined text-sm">arrow_forward</span></a>
    </div>
    
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {% if recent_history %}
            {% for item in recent_history[:3] %}
            <!-- Enhanced Glassmorphic Image Card -->
            <a href="/history" class="relative rounded-[2rem] p-6 shadow-[0_12px_40px_rgba(46,50,48,0.08)] flex flex-col justify-end h-[240px] overflow-hidden group cursor-pointer hover:shadow-[0_20px_50px_rgba(74,124,89,0.2)] transition-all duration-500 hover:-translate-y-2">
                <!-- Background Image -->
                <img src="{{ url_for('upload.uploaded_images', filename=item.image_filename) }}" class="absolute inset-0 w-full h-full object-cover transition-transform duration-700 group-hover:scale-110" onerror="this.onerror=null; this.src='/static/images/terra_texture.png'; this.classList.add('opacity-30', 'mix-blend-multiply');" alt="Scan Image" />
                
                <!-- Heavy Gradient Overlay for text readability -->
                <div class="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent"></div>
                
                <!-- Icon Badge -->
                <div class="absolute top-4 right-4 bg-white/20 backdrop-blur-md rounded-full w-10 h-10 flex items-center justify-center border border-white/20 transition-transform group-hover:scale-110 group-hover:bg-[#4a7c59] group-hover:border-transparent">
                    <span class="material-symbols-outlined text-white text-sm">{% if 'healthy' in item.prediction.name|lower %}spa{% else %}coronavirus{% endif %}</span>
                </div>
                
                <div class="relative z-10 transform transition-transform duration-500 group-hover:translate-y-0">
                    {% set crop_name = item.prediction.name.split('___')[0].replace('_', ' ') if '___' in item.prediction.name else 'Plant' %}
                    {% set disease_name = item.prediction.name.split('___')[1].replace('_', ' ') if '___' in item.prediction.name else item.prediction.name %}
                    
                    <span class="inline-block px-3 py-1 bg-white/20 backdrop-blur-md border border-white/20 text-white text-[10px] font-bold uppercase tracking-widest rounded-full mb-3 shadow-sm">{{ crop_name }}</span>
                    <h3 class="font-headline text-xl text-white font-bold tracking-tight truncate drop-shadow-md" title="{{ disease_name }}">{{ disease_name }}</h3>
                    <div class="flex items-center gap-2 mt-2 text-white/80 text-xs font-medium">
                        <span class="material-symbols-outlined text-[14px]">calendar_today</span>
                        {{ item.timestamp.split('T')[0] }}
                    </div>
                </div>
            </a>
            {% endfor %}
        {% else %}'''

pattern = r"<!-- VIEW 1: HOME HERO VIEW -->.*?\{%\s*else\s*%\}"
new_content = re.sub(pattern, new_hero + "\n        {% else %}", content, flags=re.DOTALL)

with open('app/templates/home.html', 'w', encoding='utf-8') as f:
    f.write(new_content)
