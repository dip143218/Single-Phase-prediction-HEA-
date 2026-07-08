let lastPrediction = null;
let gaugeChart = null;
let featureChart = null;

const ELEMENTS = [
"Ag","Al","Au","B","Ba","Bi","Ca","Cd","Ce","Co","Cr",
"Cu","Eu","Fe","Ga","Gd","Ge","Hg","In","Ir","Li",
"Mg","Mn","Na","Nb","Ni","Pb","Pd","Pt","Rh","Sb",
"Sc","Se","Si","Sn","Sr","Tb","Te","Ti","Tl","Y",
"Yb","Zn","Zr"
];

let selected = [];

const grid = document.getElementById("elements");
const selectedDiv = document.getElementById("selectedElements");
const totalDiv = document.getElementById("totalPercent");
const resultBox = document.getElementById("predictionResult");

// ----------------------------
// Draw Elements
// ----------------------------

function drawElements(){

    grid.innerHTML = "";

    ELEMENTS.forEach(el=>{

        const box=document.createElement("div");

        box.className="element";

        box.innerText=el;

        if(selected.find(x=>x.element===el)){
            box.classList.add("selected");
        }

        box.onclick=()=>toggleElement(el);

        grid.appendChild(box);

    });

}

// ----------------------------

function toggleElement(el){

    const idx=selected.findIndex(x=>x.element===el);

    if(idx!=-1){

        selected.splice(idx,1);

    }

    else{

        if(selected.length>=5){

            alert("Maximum 5 elements allowed.");

            return;

        }

        selected.push({

            element:el,
            composition:20

        });

    }

    drawElements();

    drawSelected();

}

// ----------------------------

function drawSelected(){

    selectedDiv.innerHTML="";

    selected.forEach((item,index)=>{

        selectedDiv.innerHTML+=`

<div class="selectedRow">

<h3>${item.element}</h3>

<input
type="number"
min="0"
max="100"
value="${item.composition}"
onchange="updateComposition(${index},this.value)">

</div>

`;

    });

    updateTotal();

}

// ----------------------------

function updateComposition(index,value){

    selected[index].composition=Number(value);

    updateTotal();

}

// ----------------------------

function updateTotal(){

    let total=0;

    selected.forEach(x=>{

        total+=Number(x.composition);

    });

    totalDiv.innerHTML=total+" %";

}

// ----------------------------

drawElements();

// ----------------------------
// Search
// ----------------------------

document.getElementById("search").addEventListener("keyup",function(){

    const keyword=this.value.toLowerCase();

    document.querySelectorAll(".element").forEach(box=>{

        if(box.innerText.toLowerCase().includes(keyword)){

            box.style.display="flex";

        }

        else{

            box.style.display="none";

        }

    });

});

// ----------------------------
// Predict Button
// ----------------------------

document.getElementById("predictBtn").onclick=async()=>{

    if(selected.length!=5){

        alert("Please select exactly 5 elements.");

        return;

    }

    let total=0;

    selected.forEach(x=>{

        total+=Number(x.composition);

    });

    if(Math.abs(total-100)>0.0001){

        alert("Total composition must equal 100%");

        return;

    }

    resultBox.innerHTML="<h2>Calculating...</h2>";

    try{

        const response=await fetch("/predict",{

            method:"POST",

            headers:{
                "Content-Type":"application/json"
            },

            body:JSON.stringify({

                elements:selected.map(x=>x.element),

                compositions:selected.map(x=>x.composition)

            })

        });

        const data=await response.json();

        console.log(data);

        if(!response.ok){

            alert(data.error);

            return;

        }

        if(!data.success){

            resultBox.innerHTML=`
            <h2>Prediction Failed</h2>
            <p>${data.error}</p>
            `;

            return;

        }

        lastPrediction=data;

        resultBox.innerHTML=`

<h2>Single Phase Probability</h2>

<h1>${data.probability}%</h1>

<h2>${data.confidence}</h2>

<p>${data.interpretation}</p>

<table>

<tr><td>ΔHmix</td><td>${data.physics.DeltaHmix}</td></tr>

<tr><td>δ Radius</td><td>${data.physics.DeltaRadius}</td></tr>

<tr><td>Ω</td><td>${data.physics.Omega}</td></tr>

<tr><td>Λ</td><td>${data.physics.Lambda}</td></tr>

<tr><td>VEC</td><td>${data.physics.VEC}</td></tr>

<tr><td>Mean Density</td><td>${data.physics.MeanDensity}</td></tr>

<tr><td>Mean Radius</td><td>${data.physics.MeanAtomicRadius}</td></tr>

<tr><td>Mean Melting Point</td><td>${data.physics.MeanMeltingPoint}</td></tr>

</table>

`;
        // ----------------------------
        // Gauge Chart
        // ----------------------------

        const gaugeCanvas = document.getElementById("gaugeChart");

        if(gaugeCanvas){

            if(gaugeChart){

                gaugeChart.destroy();

            }

            gaugeChart = new Chart(gaugeCanvas,{

                type:"doughnut",

                data:{

                    labels:["Single Phase","Others"],

                    datasets:[{

                        data:[
                            data.probability,
                            100-data.probability
                        ]

                    }]

                },

                options:{

                    responsive:true,

                    cutout:"75%",

                    plugins:{

                        legend:{

                            position:"bottom"

                        }

                    }

                }

            });

        }

        // ----------------------------
        // Feature Bar Chart
        // ----------------------------

        const featureCanvas=document.getElementById("featureChart");

        if(featureCanvas){

            if(featureChart){

                featureChart.destroy();

            }

            featureChart=new Chart(featureCanvas,{

                type:"bar",

                data:{

                    labels:[
                        "ΔHmix",
                        "δ Radius",
                        "Ω",
                        "Λ ×100",
                        "VEC"
                    ],

                    datasets:[{

                        label:"Physics Features",

                        data:[

                            Math.abs(data.physics.DeltaHmix),

                            data.physics.DeltaRadius,

                            data.physics.Omega,

                            data.physics.Lambda*100,

                            data.physics.VEC

                        ]

                    }]

                },

                options:{

                    responsive:true,

                    plugins:{

                        legend:{

                            display:false

                        }

                    },

                    scales:{

                        y:{

                            beginAtZero:true

                        }

                    }

                }

            });

        }

    }

    catch(err){

        console.error(err);

        resultBox.innerHTML=`

<h2>Backend Connection Failed</h2>

<p>${err}</p>

`;

    }

};

// -----------------------------------
// Batch Prediction
// -----------------------------------

const batchBtn=document.getElementById("batchPredictBtn");

if(batchBtn){

batchBtn.onclick=async()=>{

    const file=document.getElementById("csvFile").files[0];

    if(!file){

        alert("Please select CSV file.");

        return;

    }

    const formData=new FormData();

    formData.append("file",file);

    const response=await fetch("/predict_csv",{

        method:"POST",

        body:formData

    });

    const data=await response.json();

    if(data.success){

        window.open(data.download,"_blank");

    }

    else{

        alert(data.error);

    }

};

}

// -----------------------------------
// Download PDF
// -----------------------------------

const pdfBtn=document.getElementById("downloadReport");

if(pdfBtn){

pdfBtn.onclick=async()=>{

    if(lastPrediction==null){

        alert("Run prediction first.");

        return;

    }

    const response=await fetch("/download_report",{

        method:"POST",

        headers:{

            "Content-Type":"application/json"

        },

        body:JSON.stringify(lastPrediction)

    });

    const data=await response.json();

    if(data.success){

        window.open(data.file,"_blank");

    }

    else{

        alert(data.error);

    }

};

}