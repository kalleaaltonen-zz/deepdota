let dire_selected = []
let radiant_selected = []
let ban_selected = []

function allowDrop(ev) {
  ev.preventDefault();
}

function probFormat(n) {
  return Math.round(n * 100) + "%"
}

function randId() {
     return "x" + Math.random().toString(36).substr(2, 10);
}

function relationshipMax(picks) {
  let m = 0
  let allPicks = R.concat(picks.radiant, picks.dire)
  let [min, max] = d3.extent(R.chain(R.prop('value'), R.chain(R.prop('advantages'), allPicks)))
  m = Math.max(max, Math.abs(min))
  let [min2, max2] = d3.extent(R.chain(R.prop('value'), R.chain(R.prop('synergies'), allPicks)))
  m = Math.max(m, max2, Math.abs(min2))
  return m
}

function renderPicks(container, picks, max) {
  console.log('render', container, picks[0]);
  if(R.isEmpty(picks))
    return;
  $(container).append('<table></table>')
  let table = $(container + ' table')
  table.append(`
    <tr>
      <th class="name">Hero</th>
      <th>Synergy</th>
      <th>Advantage</th>
      <th>Win est.</th>
    </tr>
  `)
  picks.forEach(pick => {
    let synId = randId()
    let advId = randId()
    table.append(`
      <tr class="suggestion_${pick.id}" draggable="true" ondragstart="drag(event)">
        <td class="name_cell">${pick.name}</td>
        <td><svg id="${synId}"></svg></td>
        <td><svg id="${advId}"></svg></td>
        <td class="prob">${probFormat(pick.win)}</td>
      </tr>
      `)
    let values = []
    drawBars(synId, pick.synergies, max)
    drawBars(advId, pick.advantages, max)
  })
}

function update() {
  dire_selected = []
  document.querySelectorAll("#dire_list .herobox").forEach(n =>
    dire_selected.push(n.id)
  )

  radiant_selected = []
  document.querySelectorAll("#radiant_list .herobox").forEach(n =>
    radiant_selected.push(n.id)
  )

  ban_selected = []
  document.querySelectorAll("#ban_list .herobox").forEach(n =>
    ban_selected.push(n.id)
  )

  $('#radiant_prob').empty()
  $('#dire_prob').empty()
  $('#radiant_picks').empty()
  $('#dire_picks').empty()
  $('#msg').empty()
  if(R.all(R.isEmpty)([dire_selected, radiant_selected])) {
    $('.hint').show()
    $('#reset').hide()
    return
  }
  $("#spinner").show()

  let h = (radiant_selected.join(",") || '-') + '/' +
    (dire_selected.join(",") || '-') + '/' +
    (ban_selected.join(",") || '-') + '/'
  location.hash = '#' + h
  let url = 'match/' + h

  return fetch(url).then(response => {
    return response.json();
  }).then(function(data) {
    $("#spinner").hide()
    $('#reset').show()

    if(data.picks) {
      let max = relationshipMax(data.picks)
      console.log('max', max);
      renderPicks("#radiant_picks", data.picks.radiant, max)
      renderPicks("#dire_picks", data.picks.dire, max)
    }
    if(data.probs) {
      let {dire_win, radiant_win} = data.probs
      $("#radiant_prob").html(probFormat(radiant_win))
      $("#dire_prob").html(probFormat(dire_win))
    } if(data.msg) {
      $("#msg").html(data.msg)
    }
  })
}

function drag(ev) {
  let targetId
  if(ev.target.className.startsWith("suggestion_")) {
    targetId = ev.target.className.split("_")[1]
  } else {
    targetId = ev.target.id
  }
  ev.dataTransfer.setData("text", targetId);
}

function drop(ev) {
  ev.preventDefault();
  let el = ev.target
  while (!el.classList.contains("drop_target") && (el = el.parentElement));
  var target = el.getElementsByClassName("inner")[0]
  var data = ev.dataTransfer.getData("text");
  var herobox = document.getElementById(data)
  if(!target) {
    // it's being dropped back to heropool
    resetHeroBox(herobox)
  } else if(target && (target.childElementCount < 5 || target.parentElement.id === 'ban_list')) {
    target.appendChild(herobox);
  } else {
    return;
  }
  $('.hint').hide()
  update()
}

function moveHero(id, target) {
  let n = document.querySelector(`#${target} .inner`)
  let h = document.getElementById(id)
  if(h) n.appendChild(h)
}

function splitToNumbers(s) {
  if(!s) return []
  return _.filter(s.split(',').map(x => Number(x)), _.isFinite)
}

function processHash() {
  let [r,d,b] = location.hash.substring(1).split('/')
  splitToNumbers(r).forEach(id => moveHero(id, "radiant_list"))
  splitToNumbers(d).forEach(id => moveHero(id, "dire_list"))
  splitToNumbers(b).forEach(id => moveHero(id, "ban_list"))
  update()
}

function resetHeroBox(herobox) {
  let pool = document.getElementById(herobox.primary_attr)
  let afterElement
  let l = pool.children
  for(let i = 0; i < l.length; i++) {
    afterElement = l[i]
    if(afterElement && afterElement.title.localeCompare(herobox.title) == 1) {
      break
    }
  }
  if(afterElement) {
    pool.insertBefore(herobox, afterElement)
  } else { // it's the last
    pool.appendChild(herobox)
  }
}

function render() {
  return fetch('static/heroes.json').then(response => {
    return response.json()
  }).then(heroes => {
    console.log()
    heroes.sort((a,b) => a.localized_name.localeCompare(b.localized_name))
    heroes.forEach(hero => {
      var herobox = document.createElement("img")
      herobox.id = hero.id
      herobox.className = "herobox"
      herobox.draggable = "true"
      herobox.ondragstart = drag
      herobox.alt = hero.localized_name
      herobox.title = hero.localized_name
      herobox.src = hero.img
      herobox.onmouseover = function() {
        document.querySelector("#heroinfo .name").innerHTML = this.title
      }
      herobox.onmouseout = function() {
        document.querySelector("#heroinfo .name").innerHTML = ''
      }
      herobox.primary_attr = hero.primary_attr

      herobox.innerHTML = hero.localized_name

      document.getElementById(hero.primary_attr).appendChild(herobox)
    })

    processHash()
  }).catch(err => {
    console.error("heroes.json", err);
  })
}

function drawBars(containerId, data, max) {
  var width = 25 * data.length,
      height = 50;

  var x = d3.scale.ordinal()
      .rangeRoundBands([0, width], 0.1);

  var y = d3.scale.linear()
      .range([height, 0]);


  var chart = d3.select("#"+containerId)
      .attr("width", width)
      .attr("height", height);

  if(!max)
    max = d3.max(data, function(d){ return Math.abs(d.value)})

  x.domain(data.map(function(d) { return d.name; }));
  y.domain([-max, max]);

  var bar = chart.selectAll("g")
      .data(data)
    .enter().append("g")
      .attr("transform", function(d) { return "translate(" + x(d.name) + ",0)"; })

  bar.append("rect")
      .attr("y", function(d) { return y(Math.max(d.value, 0)); })
      .attr("height", function(d) { return Math.abs(y(d.value) - y(0)) })
      .attr("class", function(d) {return d.value > 0 ? "positive" : "negative" })
      .attr("width", x.rangeBand())
      .on("mouseover", function(d) {
        div.transition()
        .duration(200)
        .style("opacity", .9);
        div	.html(d.desc)
        .style("left", (d3.event.pageX) + "px")
        .style("top", (d3.event.pageY - 28) + "px");
      })
      .on("mouseout", function(d) {
          div.transition()
              .duration(500)
              .style("opacity", 0);
      });

    // Define the div for the tooltip
  var div = d3.select("body").append("div")
      .attr("class", "tooltip")
      .style("opacity", 0);

}
